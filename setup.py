""" Setup script. """
from pathlib import Path

from setuptools import setup, find_packages


def _get_long_description():
    with open(Path(__file__).parent / "README.md", "r") as f:
        return f.read()


def _get_version():
    with open(Path(__file__).parent / "muspy" / "version.py", "r") as f:
        for line in f:
            if line.startswith("__version__"):
                delimeter = '"' if '"' in line else "'"
                return line.split(delimeter)[1]
    raise RuntimeError("Cannot read version string.")


setup(
    name="muspy",
    packages=find_packages(include=["muspy", "muspy.*"], exclude=["tests"]),
    version=_get_version(),
    description="A python package for symbolic music generation.",
    long_description=_get_long_description(),
    long_description_content_type="text/markdown",
    setup_requires=["pytest-runner>=2.0,<3.0"],
    install_requires=[
        "jsonschema>=3.0",
        "music21>=5.0",
        "pretty-midi>=0.2",
        "pypianoroll>=0.2",
        "requests>=2.0",
        "tqdm>=4.0",
        "xmlschema>=1.0",
        "yamale>=2.0",
    ],
    extras_require={
        "optional": [
            "joblib>=0.15",
            "matplotlib>=1.5",
            "tensorflow-gpu>=2.0",
            "torch>=1.0",
        ],
        "dev": [
            "black>=19.0",
            "flake8-docstrings>=1.5",
            "flake8>=3.8",
            "mypy>=0.770",
            "pylint>=2.5",
            "sphinx-rtd-theme>=0.5",
            "sphinx>=3.0",
        ],
        "pytest": ["pytest>=3.0.0,<4.0"],
    },
    test_suite="tests",
)
