#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = parse_requirements("requirements.txt")

setup_requirements = [
    'pytest-runner',
]

test_requirements = parse_requirements("requirements_dev.txt")

setup(
    name='taxi_simulator',
    version='0.4.1',
    description="Agent-based taxi simulator to test strategies",
    long_description=readme + '\n\n' + history,
    author="Javi Palanca",
    author_email='jpalanca@gmail.com',
    url='https://github.com/javipalanca/taxi_simulator',
    packages=find_packages(include=['taxi_simulator']),
    entry_points={
        'console_scripts': [
            'simfleet=taxi_simulator.cli:main'
        ]
    },
    include_package_data=True,
    package_data={"taxi_simulator": ["templates"]},
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='taxi_simulator',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
