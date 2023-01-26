"""A constraint to allow flows from to a storage based on the storage level.

SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Model
from oemof.solph.components import GenericStorage
from pyomo import environ as po


def storage_level_constraint(
    model: Model,
    name: str,
    storage_component: GenericStorage,
    multiplexer_component: Bus,
    input_level_components: dict[Bus: float],
    output_level_components: dict[Bus: float],
):
    r"""
    Add constraits to implement storage content based access.

    Parameters
    ----------
    model : oemof.solph.Model
        Model to which the constraint is added.
    name : string
        Name of the multiplexer.
    storage_component : oemof.solph.components.GenericStorage
        Storage component whose content should mandate the possible inputs and outputs.
    multiplexer_component : oemof.solph.Bus
        Bus which connects the input and output levels to the storage.
    input_level_components : dictionary with oemof.solph.Bus as keys and float as values
        Dictionary of buses which act as inputs and corresponding levels
    output_level_components : dictionary with oemof.solph.Bus as keys and float as values
        Dictionary of buses which act as outputs and corresponding level
    """

