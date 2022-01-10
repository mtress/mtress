import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="mtress",
    version="2.1.0.RC1",
    author="Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR), KEHAG Energiehandel GmbH",
    packages=["mtress"],
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    zip_safe=False,
    install_requires=[
        "pyyaml >= 6.0",
        "oemof.solph >= 0.4.4",
        "oemof.thermal >= 0.0.5",
    ]
)
