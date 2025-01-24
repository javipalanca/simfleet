#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    with open(filename) as f:
        lineiter = (line.strip() for line in f)
        return [line for line in lineiter if line and not line.startswith("#")]


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = parse_requirements("requirements.txt")

setup_requirements = [
    "pytest-runner",
]

test_requirements = parse_requirements("requirements_dev.txt")

setup(
    name="simfleet",
    version="2.0.0",
    description="Agent-based fleet simulator to test strategies",
    long_description=readme + "\n\n" + history,
    author="Javi Palanca",
    author_email="jpalanca@dsic.upv.es",
    url="https://github.com/javipalanca/simfleet",
    packages=find_packages(include=["simfleet", "simfleet.*",
        "simfleet.common.*", "simfleet.common.agents.*"]),
    entry_points={"console_scripts": ["simfleet=simfleet.cli:main"]},
    include_package_data=True,
    package_data={"simfleet": ["templates"]},
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="simfleet",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
