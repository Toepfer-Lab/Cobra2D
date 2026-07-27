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
import os
import pathlib
import re
import sys

# The package uses a src-layout, so the sources live in <repo>/src.
_SRC = pathlib.Path(__file__).resolve().parents[2].joinpath("src")
sys.path.insert(0, _SRC.as_posix())

# -- Project information -----------------------------------------------------

project = 'cobra2d'
copyright = '2022, Jan-Niklas Weder'
author = 'Jan-Niklas Weder'


def _get_version() -> str:
    """Read __version__ from the package without importing it.
    """
    init = _SRC.joinpath("cobra2d", "__init__.py").read_text()
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']', init, re.MULTILINE
    )
    if match is None:
        raise RuntimeError("Unable to find __version__ in cobra2d/__init__.py")
    return match.group(1)


# The full version, including alpha/beta/rc tags, derived from the package.
release = _get_version()

# The text shown in the top-left brand of the docs (overrides "<project> <release> documentation")
html_title = 'Cobra2D'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'nbsphinx',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "cobra": ("https://cobrapy.readthedocs.io/en/latest/", None),
    "escher": ("https://escher.readthedocs.io/en/latest/", None),
}

# AutoSummary
autosummary_generate = True

# autodoc settings
add_module_names = False
autoapi_generate_api_docs = False
autoapi_add_toctree_entry = False

autoapi_dirs = ["../../src/cobra2d"]


# APIDoc
# autoapi_dirs = '../../src/cobra2d'
# apidoc_output_dir = 'reference'
# autoapi_root = 'module'
#apidoc_excluded_paths = ['tests']
#apidoc_separate_modules = False
#autoapi_generate_api_docs = True
#autoapi_add_toctree_entry = True

# auto parse md and rst
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

html_theme_options = {
    'navigation_depth' : -1
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
