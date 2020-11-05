# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os.path
import sys

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))

master_doc = "index"

# -- Project information -----------------------------------------------------

project = "MusPy"
copyright = "2020, Hao-Wen Dong"
author = "Hao-Wen Dong"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = []  # "_templates"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------


html_theme = "sphinx_rtd_theme"  # "alabaster"
html_theme_options = {"logo_only": True}
html_logo = os.path.join("images", "logo.svg")
html_context = {
    "display_github": True,
    "github_user": "salu133445",
    "github_repo": "muspy",
    "github_version": "master",
    "conf_py_path": "/doc/source/",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # '_static'

# -- Extension configurations -------------------------------------------------
autoclass_content = "both"
autodoc_typehints = "none"
autodoc_default_flags = ["members"]
autodoc_default_options = {
    "member-order": "bysource",
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "mido": ("https://mido.readthedocs.io/en/latest/", None),
    "pretty_midi": ("https://craffel.github.io/pretty-midi/", None),
    "pypianoroll": ("https://salu133445.github.io/pypianoroll/", None),
}
