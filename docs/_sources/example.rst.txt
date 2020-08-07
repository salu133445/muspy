====================
Example Music Object
====================

Here is an example of a Music object in YAML format.

.. code-block:: yaml

    metadata:
      schema_version: '0.0'
      title: Fur Elise
      creators:
        - Ludwig van Beethoven
      copyright: null
      collection: collection
      source_filename: example.yaml
      source_format: null
    resolution: 4
    tempos:
      - time: 0
        tempo: 120
    key_signatures:
      - time: 0
        root: A
        mode: minor
    time_signatures:
      - time: 0
        numerator: 3
        denominator: 8
    downbeats:
      - 4
      - 16
    lyrics:
      - time: 0
        lyric: nothing but a lyric
    annotations:
      - time: 0
        annotation: nothing but an annotation
    tracks:
      - program: 0
        is_drum: false
        name: melody
        notes:
          - time: 0
            duration: 2
            pitch: 76
            velocity: 127
          - time: 2
            duration: 2
            pitch: 75
            velocity: 127
          - time: 4
            duration: 2
            pitch: 76
            velocity: 127
          - time: 6
            duration: 2
            pitch: 75
            velocity: 127
          - time: 8
            duration: 2
            pitch: 76
            velocity: 127
          - time: 10
            duration: 2
            pitch: 71
            velocity: 127
          - time: 12
            duration: 2
            pitch: 74
            velocity: 127
          - time: 14
            duration: 2
            pitch: 72
            velocity: 127
          - time: 16
            duration: 2
            pitch: 69
            velocity: 127
        lyrics:
          - time: 0
            lyric: nothing but a lyric
        annotations:
          - time: 0
            annotation: nothing but an annotation
