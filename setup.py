"""Setup script."""
from pathlib import Path

from setuptools import find_packages, setup


def _get_long_description():
    with open(str(Path(__file__).parent / "README.md"), "r") as f:
        return f.read()


def _get_version():
    with open(str(Path(__file__).parent / "muspy/version.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                delimeter = '"' if '"' in line else "'"
                return line.split(delimeter)[1]
    raise RuntimeError("Cannot read version string.")


VERSION = _get_version()

setup(
    name="muspy",
    version=VERSION,
    author="Hao-Wen Dong",
    author_email="salu.hwdong@gmail.com",
    description="A toolkit for symbolic music generation",
    long_description=_get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/salu133445/muspy",
    download_url=(
        f"https://github.com/salu133445/muspy/archive/v{VERSION}.tar.gz"
    ),
    project_urls={"Documentation": "https://salu133445.github.io/muspy/"},
    license="MIT",
    keywords=[
        "music",
        "audio",
        "music-generation",
        "music-information-retrieval",
    ],
    packages=find_packages(include=["muspy", "muspy.*"], exclude=["tests"]),
    install_requires=[
        "PyYAML>=3.0",
        "bidict>=0.21",
        "joblib>=0.15",
        "matplotlib>=1.5",
        "miditoolkit>=0.1",
        "mido>=1.0",
        "music21>=6.0",
        "pretty-midi>=0.2",
        "pypianoroll>=1.0",
        "requests>=2.0",
        "tqdm>=4.0",
    ],
    extras_require={
        "dev": [
            "black>=19.0",
            "flake8-docstrings>=1.5",
            "flake8>=3.8",
            "mypy>=0.900",
            "pylint>=2.5",
            "sphinx-rtd-theme>=0.5",
            "sphinx>=3.0",
        ],
        "optional": ["tensorflow>=2.0", "torch>=1.0"],
        "schema": ["jsonschema>=3.0", "xmlschema>=1.0", "yamale>=2.0"],
        "test": ["pytest>=6.0", "pytest-cov>=2.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.6",
)
