#!/usr/bin/env python

import os

from setuptools import find_packages, setup


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding="utf-8") as file:
        return file.read()


version = "0.3.3"
if "-dev" in version:
    dev_status = "Development Status :: 3 - Alpha"
elif "-beta" in version:
    dev_status = "Development Status :: 4 - Beta"
else:
    dev_status = "Development Status :: 5 - Production/Stable"


setup(
    name="cognite-synthetic-tags",
    version=version,
    description=(
        "An easy way to retrieve values from CDF and execute mathematical"
        " operations on them at the same time."
    ),
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    author="Fran Hrzenjak",
    author_email="fran.hrzenjak@cognite.com",
    license="Apache License 2.0",
    platforms=["OS Independent"],
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "cognite-sdk>=2.26,<3",
    ],
    classifiers=[
        dev_status,
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=True,
)
