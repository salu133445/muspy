========
Datasets
========

MusPy provides an easy-to-use dataset management system. Each supported dataset comes with a class inherited from the base MusPy Dataset class. MusPy also provides interfaces to PyTorch and TensorFlow for creating input pipelines for machine learning. Here is an example of preparing training data in the piano-roll representation from the NES Music Database using MusPy. ::

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


.. toctree::
    :hidden:

    iterator
    datasets
    base
    local
    remote
