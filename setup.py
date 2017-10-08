#! /usr/bin/env python

from setuptools import setup

setup(
    name='prmcore',
    version='0.1.0',
    description='Library containing core objects and methods for Project Repository Manager (prm)',
    keywords='data science project manager ',
    author='Heiko Mueller',
    author_email='heiko.muller@gmail.com',
    url='https://github.com/heikomuller/prm-core',
    license='GPLv3',
    packages=['prmcore'],
    package_data={'': ['LICENSE']},
    install_requires=['pyyaml']
)
