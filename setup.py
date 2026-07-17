"""Backward-compatible setup.py shim.

Modern builds should use ``pip install .`` which reads ``pyproject.toml``.
This file exists only for legacy tooling that expects ``python setup.py``.
"""

from setuptools import setup

setup()
