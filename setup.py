#!/usr/bin/env python

from distutils.core import setup

setup(
    name="amcatclient",
    version='3.4.5',
    description="Python bindings for the AmCAT API",
    author="Wouter van Atteveldt",
    author_email="wouter@vanatteveldt.com",
    packages=["amcatclient"],
    keywords = ["amcat", "client"],
    download_url="https://github.com/amcat/amcatclient/tarball/3.4.1",
    url="http://github.com/amcat/amcatclient",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "requests==2.9.1",
        "six==1.10.0"
    ],
)
