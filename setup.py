import re
from pathlib import Path

from setuptools import setup, find_packages

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
    install_requires=["ete3"],
    python_requires=">=3.6",
)
