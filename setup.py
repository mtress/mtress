import os
from setuptools import find_packages, setup


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name="mtress",
    version="2.1.0",
    url="https://github.com/mtress/mtress",
    author="Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)",
    author_email="patrik.schoenfeldt@dlr.de",
    packages=find_packages(),
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    zip_safe=False,
    install_requires=[
        "pyyaml >= 6.0",
        "oemof.solph >= 0.4.4",
        "oemof.thermal >= 0.0.5",
    ],
)
