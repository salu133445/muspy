"""Audio output interface."""
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Union

import numpy as np
from numpy import ndarray

from ..external import get_musescore_soundfont_path
from .midi import write_midi

if TYPE_CHECKING:
    from ..music import Music


def _check_soundfont(soundfont_path):
    if soundfont_path is None:
        soundfont_path = get_musescore_soundfont_path()
    else:
        soundfont_path = Path(soundfont_path)
    if not soundfont_path.exists():
        raise RuntimeError(
            "Soundfont not found. Please download it by "
            "`muspy.download_musescore_soundfont()`."
        )
    return soundfont_path


def synthesize(
    music: "Music",
    soundfont_path: Union[str, Path] = None,
    rate: int = 44100,
    gain: float = 1,
    options: str = None,
) -> ndarray:
    """Synthesize a Music object to raw audio.

    Parameters
    ----------
    music : :class:`muspy.Music`
        Music object to write.
    soundfont_path : str or Path, optional
        Path to the soundfount file. Defaults to the path to the
        downloaded MuseScore General soundfont.
    rate : int, default: 44100
        Sample rate (in samples per sec).
    gain : float, default: 1
        Master gain (`-g` option) for Fluidsynth. The value must be
        in between 0 and 10, excluding. This can be used to avoid
        clipping.
    options : str, optional
        Additional options to be passed to the FluidSynth call. The
        full command called is: `fluidsynth -T raw -F- -r {rate}
        -g {gain} -i {soundfont_path} {options} {midi_path}`.

    Returns
    -------
    ndarray, dtype=int16, shape=(?, 2)
        Synthesized waveform.

    """
    # Check soundfont
    soundfont_path = _check_soundfont(soundfont_path)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:

        # Write the Music object to a temporary MIDI file
        midi_path = Path(temp_dir) / "temp.mid"
        write_midi(midi_path, music)

        # Synthesize the MIDI file using fluidsynth
        option_list = options.split(" ") if options is not None else []
        result = subprocess.run(
            [
                "fluidsynth",
                "-T",
                "raw",
                "-F-",
                "-r",
                str(rate),
                "-g",
                str(gain),
                "-i",
                str(soundfont_path),
            ]
            + option_list
            + [str(midi_path)],
            check=True,
            stdout=subprocess.PIPE,
        )

    # Decode bytes to waveform
    waveform = np.frombuffer(result.stdout, np.int16).reshape(-1, 2)

    return waveform


def write_audio(
    path: Union[str, Path],
    music: "Music",
    audio_format: str = "auto",
    soundfont_path: Union[str, Path] = None,
    rate: int = 44100,
    gain: float = 1,
    options: str = None,
):
    """Write a Music object to an audio file.

    Supported formats include WAV, AIFF, FLAC and OGA.

    Parameters
    ----------
    path : str or Path
        Path to write the audio file.
    music : :class:`muspy.Music`
        Music object to write.
    audio_format : str, default: 'auto'
        File format to write. Defaults to infer from the extension.
    soundfont_path : str or Path, optional
        Path to the soundfount file. Defaults to the path to the
        downloaded MuseScore General soundfont.
    rate : int, default: 44100
        Sample rate (in samples per sec).
    gain : float, default: 1
        Master gain (`-g` option) for Fluidsynth. The value must be
        in between 0 and 10, excluding. This can be used to avoid
        clipping.
    options : str, optional
        Additional options to be passed to the FluidSynth call. The
        full command called is: `fluidsynth -ni -F {path}
        -T {audio_format} -r {rate} -g {gain} -i {soundfont_path}
        {options} {midi_path}`.

    """
    # Check soundfont
    soundfont_path = _check_soundfont(soundfont_path)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:

        # Write the Music object to a temporary MIDI file
        midi_path = Path(temp_dir) / "temp.mid"
        write_midi(midi_path, music)

        # Synthesize the MIDI file using fluidsynth
        option_list = options.split(" ") if options is not None else []
        subprocess.run(
            [
                "fluidsynth",
                "-ni",
                "-F",
                str(path),
                "-T",
                audio_format,
                "-r",
                str(rate),
                "-g",
                str(gain),
                str(soundfont_path),
            ]
            + option_list
            + [str(midi_path)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
