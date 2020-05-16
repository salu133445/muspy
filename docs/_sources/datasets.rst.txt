========
Datasets
========

Here is a list of the supported datasets.

============================ ======== ====== ======= ========= ====== ====== ==========
Dataset                      Format   Hours  Songs   Genre     Melody Chords Multitrack
============================ ======== ====== ======= ========= ====== ====== ==========
Lakh MIDI Dataset            MIDI      >5000 174,592 misc      \*     \*     \*
MAESTRO Dataset              MIDI     201.21   1,282 classical
Wikifonia Lead Sheet Dataset MusicXML 199.12   6,434 misc      O      O
Essen Folk Song Dataset      ABC       56.62   9,034 folk      O      O
NES Music Database           MIDI      46.11   5,278 game      O             O
music21's Corpus             misc      19.30    649  misc      \*            \*
Hymnal Tune Dataset          MIDI      18.72   1,754 hymn      O
Hymnal Dataset               MIDI      17.48   1,721 hymn
Nottingham Database          ABC       10.54   2,036 folk      O      O
JSBach Chorale Dataset       MIDI       3.86     382 classical               O
music21's JSBach Corpus      MusicXML   3.46     410 classical               O
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


Base Dataset Class
==================

.. autoclass:: muspy.Dataset
    :noindex:


MusicDataset Class
==================

.. autoclass:: muspy.MusicDataset
    :noindex:


FolderDataset Class
===================

.. autoclass:: muspy.FolderDataset
    :noindex:


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
