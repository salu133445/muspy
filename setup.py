"""Setup script."""
from pathlib import Path

from setuptools import find_packages, setup


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
    description="A toolkit for symbolic music generation.",
    long_description=_get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    install_requires=[
        "matplotlib>=1.5",
        "mido>=1.0",
        "music21>=5.0",
        "pretty-midi>=0.2",
        "pypianoroll>=0.5",
        "requests>=2.0",
        "tqdm>=4.0",
    ],
    extras_require={
        "schemas": ["jsonschema>=3.0", "xmlschema>=1.0", "yamale>=2.0"],
        "joblib": ["joblib>=0.15"],
        "tensorflow": ["tensorflow-gpu>=2.0"],
        "pytorch": ["torch>=1.0"],
        "dev": [
            "black>=19.0",
            "flake8-docstrings>=1.5",
            "flake8>=3.8",
            "mypy>=0.770",
            "pylint>=2.5",
            "pytest >= 5.0",
            "pytest-cov >= 2.0",
            "sphinx-rtd-theme>=0.5",
            "sphinx>=3.0",
        ],
    },
)
