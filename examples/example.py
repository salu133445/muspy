"""Example script for training an autoregressive model."""
import argparse
import math
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

import muspy

DATASET_KEYS = [
    "lmd",
    "wikifonia",
    "nes",
    "jsb",
    "maestro",
    "hymnal",
    "hymnal_tune",
    "music21",
    "music21jsb",
    "nmd",
    "essen",
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MusPy Experiment")

    # Data
    parser.add_argument(
        "-d", "--data", type=str, default="", help="Dataset identifier.",
    )
    parser.add_argument(
        "-r", "--root", type=str, default="", help="Root path to the dataset.",
    )

    # Model
    parser.add_argument(
        "-sl", "--seq_len", type=int, default=64, help="Sequence length."
    )
    parser.add_argument(
        "-es",
        "--embedding_size",
        type=int,
        default=128,
        help="Size of token embeddings.",
    )
    parser.add_argument(
        "-hs",
        "--hidden_size",
        type=int,
        default=128,
        help="Number of hidden units per layer.",
    )
    parser.add_argument(
        "-nl", "--n_layers", type=int, default=2, help="Number of layers."
    )
    parser.add_argument(
        "-do",
        "--dropout",
        type=float,
        default=0.5,
        help="Dropout ratio (set to 0 to disable dropout).",
    )

    # Training
    parser.add_argument(
        "--steps",
        type=str,
        default=50000,
        help="Maximum steps to train the model.",
    )
    parser.add_argument(
        "-bs",
        "--batch_size",
        type=int,
        default=16,
        metavar="N",
        help="Batch size for training.",
    )
    parser.add_argument(
        "-ebs",
        "--eval_batch_size",
        type=int,
        default=10,
        metavar="N",
        help="Batch size for evaluation.",
    )
    parser.add_argument(
        "--lr", type=float, default=0.001, help="Initial learning rate."
    )

    # Others
    parser.add_argument(
        "--cuda", action="store_true", help="Whether to use CUDA."
    )
    parser.add_argument(
        "--n_jobs",
        type=int,
        default=1,
        help="Number of workers to use for data loader.",
    )
    parser.add_argument(
        "-ld", "--log_dir", type=str, help="Log directory.",
    )
    parser.add_argument(
        "-md", "--model_dir", type=str, help="Model directory.",
    )
    parser.add_argument(
        "-li",
        "--log_steps",
        type=int,
        default=10,
        metavar="N",
        help="Logging interval.",
    )
    parser.add_argument(
        "-vi",
        "--val_steps",
        type=int,
        default=100,
        metavar="N",
        help="Validation interval.",
    )

    return parser.parse_args()


def get_dataset(key, root):
    if key == "lmd":
        return muspy.LakhMIDIDataset(root)
    if key == "wikifonia":
        return muspy.WikifoniaDataset(root)
    if key == "nes":
        return muspy.NESMusicDatabase(root)
    if key == "jsb":
        return muspy.JSBChoralesDataset(root)
    if key == "maestro":
        return muspy.MAESTRODatasetV2(root)
    if key == "hymnal":
        return muspy.HymnalDataset(root)
    if key == "hymnal_tune":
        return muspy.HymnalDataset(root)
    if key == "music21":
        return muspy.MusicDataset(root)
    if key == "music21jsb":
        return muspy.Music21Dataset("bach")
    if key == "nmd":
        return muspy.NottinghamDatabase(root)
    if key == "essen":
        return muspy.EssenFolkSongDatabase(root)
    raise ValueError("Unrecognized dataset name.")


def repackage_hidden(h):
    """Wrap hidden states in new Tensors, to detach them from history."""
    if isinstance(h, torch.Tensor):
        return h.detach()
    else:
        return tuple(repackage_hidden(v) for v in h)


class LSTMModel(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(
        self, n_tokens, input_size, hidden_size, n_layers, dropout=0.5
    ):
        super().__init__()
        self.n_tokens = n_tokens
        self.drop = nn.Dropout(dropout)
        self.encoder = nn.Embedding(n_tokens, input_size)
        self.rnn = nn.LSTM(input_size, hidden_size, n_layers, dropout=dropout)
        self.decoder = nn.Linear(hidden_size, n_tokens)

        self.init_weights()

        self.hidden_size = hidden_size
        self.n_layers = n_layers

    def init_weights(self):
        """Initialize weights."""
        self.encoder.weight.data.uniform_(-0.1, 0.1)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-0.1, 0.1)

    def forward(self, x, hidden):
        """Forward pass."""
        emb = self.drop(self.encoder(x))
        output, hidden = self.rnn(emb, hidden)
        output = self.drop(output)
        decoded = self.decoder(output)
        decoded = decoded.view(-1, self.n_tokens)
        return F.log_softmax(decoded, dim=1), hidden

    def init_hidden(self, bsz):
        """Initialize hidden states."""
        weight = next(self.parameters())
        return (
            weight.new_zeros(self.n_layers, bsz, self.hidden_size),
            weight.new_zeros(self.n_layers, bsz, self.hidden_size),
        )


def main():
    """Main function."""
    args = parse_args()

    if torch.cuda.is_available():
        if not args.cuda:
            warnings.warn(
                "Aa CUDA device is available, you might want to run with "
                "--cuda option."
            )

    device = torch.device("cuda" if args.cuda else "cpu")

    # Data ====================================================================
    if args.data not in DATASET_KEYS:
        raise ValueError("Unrecognized dataset name.")

    music_dataset = get_dataset(args.data, args.root)
    split_filename = Path(args.root) / args.data / "splits.txt"

    eos = 356

    def factory(music):
        """Factory that turn a Music object into input-target pair."""
        # Get event representation and remove velocity events
        encoded = music.to_event_representation()
        encoded = encoded[encoded < eos].astype(np.int)

        # Pad to meet the desired length
        if len(encoded) > args.seq_len:
            start = np.random.randint(encoded.shape[0] - args.seq_len + 1)
            encoded = encoded[start : (start + args.seq_len)]
            encoded = np.append(encoded, eos)
        elif len(encoded) < args.seq_len:
            to_concat = np.ones(args.seq_len - encoded.shape[0] + 1, np.int)
            to_concat.fill(eos)
            encoded = np.concatenate((encoded, to_concat))
        else:
            encoded = np.append(encoded, 129)

        return encoded[:-1], encoded[1:]

    train_, val_, test_ = music_dataset.to_pytorch_dataset(
        factory=factory, split_filename=split_filename, splits=(0.8, 0.1, 0.1)
    )
    train_data = DataLoader(
        train_,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=args.n_jobs,
    )
    val_data = DataLoader(
        val_,
        batch_size=args.eval_batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=args.n_jobs,
    )
    test_data = DataLoader(
        test_,
        batch_size=args.eval_batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=args.n_jobs,
    )

    # Model ===================================================================
    n_tokens = eos + 1

    model = LSTMModel(
        n_tokens, args.emsize, args.hidden_size, args.n_layers, args.dropout,
    ).to(device)

    criterion = nn.NLLLoss()

    # Training ================================================================
    n_val_trials = 100

    def evaluate(data_source):
        """Wrapper for evaluation (test or train)."""
        model.eval()
        val_total_loss = 0.0
        val_hidden = model.init_hidden(args.eval_batch_size)
        with torch.no_grad():
            val_loader = iter(data_source)
            val_trial = 0
            while val_trial < n_val_trials:
                try:
                    val_data_, val_targets = val_loader.next()
                except StopIteration:
                    val_loader = iter(data_source)
                    val_data_, val_targets = val_loader.next()
                val_data_ = val_data_.t().to(device)
                val_targets = val_targets.t().reshape(-1).to(device)

                val_output, val_hidden = model(val_data_, val_hidden)
                val_hidden = repackage_hidden(val_hidden)
                val_total_loss += (
                    len(val_data_) * criterion(val_output, val_targets).item()
                )
                val_trial += 1
        return val_total_loss / (n_val_trials * args.eval_batch_size - 1)

    # Make sure directories exist
    model_dir = Path(args.model_dir)
    log_dir = Path(args.log_dir)
    (model_dir / args.data).mkdir(exist_ok=True)
    (log_dir / args.data).mkdir(exist_ok=True)
    (log_dir / args.data / args.model).mkdir(exist_ok=True)

    # Open log files
    log_file = open(str(log_dir / args.data / args.model / "train.log"), "w")
    val_log_file = open(
        str(log_dir / args.data / args.model / "validation.log"), "w"
    )

    # Write headers to log files
    log_file.write("# step, loss, perplexity\n")
    val_log_file.write("# step, loss, perplexity\n")

    # Initialization
    train_loader = iter(train_data)
    best_val_loss = None
    optim = torch.optim.Adam(model.parameters(), args.lr)
    model_filename = str(model_dir / args.data / "{}.pt".format(args.model))

    step = 0

    # At any point you can hit Ctrl + C to break out of training early.
    try:
        print("Start training...")
        while step < args.steps:

            total_loss = 0.0
            start_time = time.time()
            cycle_start_time = time.time()
            hidden = model.init_hidden(args.batch_size)
            while step < args.steps:
                try:
                    data, targets = train_loader.next()
                except StopIteration:
                    train_loader = iter(train_data)
                    data, targets = train_loader.next()
                data = data.t().to(device)
                targets = targets.t().reshape(-1).to(device)

                model.train()
                model.zero_grad()
                hidden = repackage_hidden(hidden)
                output, hidden = model(data, hidden)
                loss = criterion(output, targets)
                loss.backward()

                optim.step()

                total_loss += loss.item()

                # Logger
                if step and step % args.log_interval == 0:
                    cur_loss = total_loss / args.log_interval
                    elapsed = time.time() - start_time
                    print(
                        "| step {:5d} | ms/batch {:5.2f} | loss {:5.2f} | "
                        "ppl {:8.2f}".format(
                            step,
                            elapsed * 1000 / args.log_interval,
                            cur_loss,
                            math.exp(cur_loss),
                        )
                    )
                    log_file.write(
                        "{}, {}, {}\n".format(
                            step, cur_loss, math.exp(cur_loss)
                        )
                    )
                    total_loss = 0.0
                    start_time = time.time()

                # Validation
                if step and step % args.val_interval == 0:
                    val_loss = evaluate(val_data)
                    print("-" * 80)
                    print(
                        "| step {:5d} | time: {:5.2f}s | valid loss {:5.2f} | "
                        "valid ppl {:8.2f}".format(
                            step,
                            (time.time() - cycle_start_time),
                            val_loss,
                            math.exp(val_loss),
                        )
                    )
                    val_log_file.write(
                        "{}, {}, {}\n".format(
                            step, val_loss, math.exp(val_loss)
                        )
                    )
                    cycle_start_time = time.time()
                    print("-" * 80)

                    # Save the model if the validation loss is the best
                    # we've seen so far.
                    if not best_val_loss or val_loss < best_val_loss:
                        with open(model_filename, "wb") as f:
                            torch.save(model, f)
                        best_val_loss = val_loss

                step += 1

    except KeyboardInterrupt:
        print("-" * 80)
        print("Exiting from training early")

    # Close files
    log_file.close()
    val_log_file.close()

    # Load the best saved model.
    with open(model_filename, "rb") as f:
        model = torch.load(f)
        model.rnn.flatten_parameters()

    # Run on test data.
    test_loss = evaluate(test_data)
    print("=" * 80)
    print(
        "| End of training | test loss {:5.2f} | test ppl {:8.2f}"
        "".format(test_loss, math.exp(test_loss))
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
