#!/usr/bin/env python

from distutils.core import setup

setup(
    version='0.10',
    name="amcatclient",
    description="Python bindings for the AmCAT API",
    author="Wouter van Atteveldt",
    author_email="wouter@vanatteveldt.com",
    packages=["amcatclient"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "requests>=2.5.1"
    ],
)
