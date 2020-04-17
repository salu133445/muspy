# pseudo code
import argparse
from muspy.datasets import LakhMIDIDataset
from torch.utils.data import DataLoader


def format_processing_fn():
    """
    a custom representation functions ?
    :return:
    """
    pass


if __name__== "__main__":
    parser = argparse.ArgumentParser(
        description='Train a model on LakhMIDI dataset.')
    parser.add_argument('--data', default='.data',
                        help='data directory (default=.data)')
    parser.add_argument('--max-epoch', default=10, type=int)
    parser.add_argument('--save-midi-freq', default=100, type=int)
    config = parser.parse_args()
    device = config.device

    data_handler = LakhMIDIDataset(splits=['trainset', 'testset'], # the dataset should handle whether there's already a split or not
                                   transform=[], # a list of function
                                   )

    # can be pytorch or tensorflow
    LakhMIDIDataset.set_frontend('pytorch')
    # this would change what data_handler.[train|valid|test]set returns
    # other formats can be event-based, custom
    LakhMIDIDataset.set_output_format(preset='note')
    # or use python `register` method to register a new processing method
    LakhMIDIDataset.set_output_format(custom_fn=format_processing_fn)
    # set midi output path

    config.n_input = len(data_handler.pitch2idx)

    # everything after DataLoader should be quantized and indexed
    train_data = DataLoader(data_handler.trainset)
    test_data = DataLoader(data_handler.testset)

    model = RNNModel(n_input=config.n_input)

    # training
    for ep in range(config.max_epoch):
        for i, (pitch, dur) in enumerate(train_data):
            pitch, dur = pitch.to(device), dur.to(device)
            output = model(pitch, dur)
            # ... omitting training details

    for i, (pitch, dur) in enumerate(test_data):
        pitch, dur = pitch.to(device), dur.to(device)
        output = model(pitch, dur)

        # ... omitting training details

        # at least one metrics ?
        res = muspy.metrics.BLEU(pitch, dur, output)
        print("BLEU scores: \t", res)

        if i % config.save_midi_freq == 0:
            pitch, midi = data_handler.idx2pitch(output, requires_midi=True)
            muspy.save_midi(midi, 'path-to-save-folder')

        # potential visualization here