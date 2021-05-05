import re
from pathlib import Path

from setuptools import setup, find_packages


def get_version():
    """Get version number from __init__.py"""
    version_file = Path(__file__).resolve().parent / "cblaster" / "__init__.py"
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read_text(), re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Failed to find version string")


setup(
    name="fungphy",
    author="Cameron Gilchrist",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=["ete3", "flask", "flask-sqlalchemy", "flask-admin"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["fungphy=fungphy.main:main"]},
)
