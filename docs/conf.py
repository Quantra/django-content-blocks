# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

import django

if os.getenv("READTHEDOCS", default=False) == "True":
    sys.path.insert(0, os.path.abspath(".."))
    sys.path.insert(0, os.path.abspath("../content_blocks"))
    sys.path.insert(0, os.path.abspath("../example"))
    os.environ["DJANGO_READ_DOT_ENV_FILE"] = "True"
    os.environ["USE_DOCKER"] = "no"
else:
    sys.path.insert(0, os.path.abspath("/app"))
    sys.path.insert(0, os.path.abspath("/app/content_blocks"))
    sys.path.insert(0, os.path.abspath("/app/example"))

os.environ["DJANGO_SETTINGS_MODULE"] = "example.settings.docs"
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Django Content Blocks"
copyright = "2023, Vince Coleman"
author = "Vince Coleman"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.images",
]

images_config = {
    "override_image_directive": True,
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
