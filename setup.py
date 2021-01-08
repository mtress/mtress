import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="meta_model",
    version="0.0.0",
    author="some guys",
    packages=["meta_model"],
    long_description=read("README.md"),
    long_description_content_type="text/x-rst",
    zip_safe=False,
    install_requires=[
        "oemof.solph >= 0.4",
        "oemof.thermal >= 0.0.4"
    ]
)
