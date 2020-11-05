==============
Metadata Class
==============

The :class:`muspy.Metadata` class is a container for metadata.

=============== ========================= =========== =======
Attributes      Description               Type        Default
=============== ========================= =========== =======
schema_version  Schema version            str         '0.0'
title           Song title                str
creators        Creators(s) of the song   list of str []
copyright       Copyright notice          str
collection      Name of the collection    str
source_filename Name of the source file   str
source_format   Format of the source file str
=============== ========================= =========== =======

.. autoclass:: muspy.Metadata
    :noindex:
    :inherited-members:
