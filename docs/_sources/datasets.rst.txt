========
Datasets
========

Here is a list of the supported datasets.

============================ ======== ====== ======= ========= ====== ====== ==========
Dataset                      Format   Hours  Songs   Genre     Melody Chords Multitrack
============================ ======== ====== ======= ========= ====== ====== ==========
Lakh MIDI Dataset            MIDI      >5000 174,533 misc      \*     \*     \*
MAESTRO Dataset              MIDI     201.21   1,282 classical
Wikifonia Lead Sheet Dataset MusicXML 198.40   6,405 misc      O      O
Essen Folk Song Dataset      ABC       56.62   9,034 folk      O      O
NES Music Database           MIDI      46.11   5,278 game      O             O
Hymnal Tune Dataset          MIDI      18.74   1,756 hymn      O
Hymnal Dataset               MIDI      17.50   1,723 hymn
music21's Corpus             misc      16.86     613 misc      \*            \*
Nottingham Database          ABC       10.54   1,036 folk      O      O
music21's JSBach Corpus      MusicXML   3.46     410 classical               O
JSBach Chorale Dataset       MIDI       3.21     382 classical               O
============================ ======== ====== ======= ========= ====== ====== ==========

(Asterisk marks indicate partial support.)

Here is an illustration of the two internal processing modes for iterating over
a MusPy Dataset object.

.. image:: images/on_the_fly.svg
    :align: center
    :width: 475px

.. image:: images/preconverted1.svg
    :align: center
    :width: 500px

.. image:: images/preconverted2.svg
    :align: center
    :width: 475px


Example Usage
=============

.. code-block::

    import muspy

    # Download and extract the dataset
    nes = muspy.NESMusicDatabase("data/nes/", download_and_extract=True)

    # Convert the dataset to MusPy Music objects
    nes.convert()

    # Iterate over the dataset
    for music in nes:
        do_something(music)

    # Convert to a PyTorch dataset
    dataset = nes.to_pytorch_dataset(representation="pianoroll")


Base Dataset Classes
====================

.. autoclass:: muspy.Dataset
    :noindex:

.. autoclass:: muspy.RemoteDataset
    :noindex:


Local Dataset Classes
=====================

.. autoclass:: muspy.FolderDataset
    :noindex:

.. autoclass:: muspy.MusicDataset
    :noindex:

.. autoclass:: muspy.ABCFolderDataset
    :noindex:


Remote Dataset Classes
======================

.. autoclass:: muspy.RemoteFolderDataset
    :noindex:

.. autoclass:: muspy.RemoteMusicDataset
    :noindex:

.. autoclass:: muspy.RemoteABCFolderDataset
    :noindex:
