"""Visulisation of energy system."""

import re
from shutil import rmtree

import graphviz
import imageio
from oemof.solph import Bus
from oemof.solph.components import Converter, GenericStorage, Sink, Source

from ._util import update_in_dict

# Define shapes for the component types
SHAPES = {
    Source: "trapezium",
    Sink: "invtrapezium",
    Bus: "ellipse",
    Converter: "octagon",
    GenericStorage: "cylinder",
}
