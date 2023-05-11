# -*- coding: utf-8 -*-

"""A constraint to have one common limit for several components.

SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT

"""


from typing import Dict, Tuple

from oemof.solph import Bus, Model
from oemof.solph.components import GenericStorage
from pyomo import environ as po
from oemof.network.network import Node


def storage_multiplexer_constraint(
    model: Model,
    name: str,
    storage_component: GenericStorage,
    multiplexer_bus: Bus,
    input_levels: dict[Node, float] = None,
    output_levels: dict[Node, float] = None,
):
    r"""
    Add constraits to implement a storage content dependent multiplexer.

    Parameters
    ----------
    model : oemof.solph.Model
        Model to which the constraint is added.
    name : string
        Name of the multiplexer.
    storage_bus : oemof.solph.components.GenericStorage
        Storage component whose content should mandate the possible inputs and outputs.
    multiplexer_bus : oemof.solph.Bus
        Bus which connects the input and output levels to the storage.
    input_levels : dict[oemof.network.network.Node, float]
        Mapping of storage content levels to the corresponding input node, e.g. for a
        given value in this list, the corresponding input can be
        active if the storage content is lower than this value.
    output_levels : dict[oemof.network.network.Node, float]
        Mapping of storage content levels to the corresponding output node, e.g. for a
        given value in this list, the corresponding output can be
        active if the storage content is higher than this value.
    """
    # TODO: Add example.

    if not input_levels.values() == output_levels.values():
        raise KeyError("Input and output levels must be identical")

    # http://yetanothermathprogrammingconsultant.blogspot.com/2015/10/piecewise-linear-functions-in-mip-models.html
    # Helper variables
    levels = list(sorted(input_levels.values()))

    intervals = {
        f"{name}_interval_{i:02d}": (left, right)
        for i, (left, right) in enumerate(zip(levels[:-1], levels[1:]))
    }

    # Set for indexing the intervals (each interval is represented by its lower bound)
    def init_interval_indices(model):
        return [
            (interval, timestep)
            for timestep in model.TIMESTEPS
            for interval in intervals
        ]

    interval_indices = po.Set(dimen=2, ordered=True, initialize=init_interval_indices)
    setattr(model, f"{name}_interval_indices", interval_indices)

    # Binary variable indicating active interval
    active_interval = po.Var(interval_indices, domain=po.Binary, bounds=(0, 1))
    setattr(model, f"{name}_active_interval", active_interval)

    # Allow exactly one interval to be active
    def init_active_interval_constraint(_, timestep):
        expr = 0
        for interval in intervals:
            expr += active_interval[interval, timestep]

        return expr == 1

    setattr(
        model,
        f"{name}_active_interval_constraint",
        po.Constraint(model.TIMESTEPS, rule=init_active_interval_constraint),
    )

    # Set for indexing the weight variables
    def init_level_indices(model):
        return [(level, timestep) for timestep in model.TIMESTEPS for level in levels]

    level_indices = po.Set(dimen=2, ordered=True, initialize=init_level_indices)
    setattr(model, f"{name}_level_indices", level_indices)

    # Weight variable
    weights = po.Var(level_indices, bounds=(0, 1))
    setattr(model, f"{name}_weights", weights)

    # Constrain weight variables to be non-zero only when the corresponding levels
    # sourround the active interval
    def init_weight_constraint(_, level, timestep):
        expr = 0
        expr += weights[level, timestep]

        adjacent_intervals = [
            interval
            for interval, boundaries in intervals.items()
            if level in boundaries
        ]

        for interval in adjacent_intervals:
            expr -= active_interval[interval, timestep]

        return expr <= 0

    setattr(
        model,
        f"{name}_weight_constraints",
        po.Constraint(level_indices, rule=init_weight_constraint),
    )

    # Couple the weigths with the storage content, i.e.
    #   levels[n] * weights[n] + levels[n+1] * weights[n+1] == storage_content
    # With the constraint above this means
    #     weigths[n] > 0 and weigths[n+1] > 0
    # only if
    #     levels[n] <= storage_content <= levels[n+1]
    def couple_levels_with_storage(model, timestep):
        expr = 0
        for level in levels:
            expr += weights[level, timestep] * level

        expr -= model.GenericStorageBlock.storage_content[storage_component, timestep]
        return expr == 0

    setattr(
        model,
        f"{name}_weights_coupling",
        po.Constraint(model.TIMESTEPS, rule=couple_levels_with_storage),
    )

    # Constrain the weigth sum to one
    def constrain_weight_sum(_, timestep):
        expr = 0
        for level in levels:
            expr += weights[level, timestep]

        expr -= 1
        return expr == 0

    setattr(
        model,
        f"{name}_weight_sum_constraint",
        po.Constraint(model.TIMESTEPS, rule=constrain_weight_sum),
    )

    # Now we can constrain the input and output flows
    # Helper mapping the levels to the input components
    input_energy = {upp: upp - low for low, upp in zip(levels[:-1], levels[1:])}

    # Define constraints on the input flows
    def constrain_input_flows(model, flow_level, timestep):
        expr = 0

        # Energy of the interval below the flow level
        expr -= sum(weights[level, timestep] for level in levels if level < flow_level)
        expr *= input_energy.get(flow_level, 0)

        # Energy which is extracted in this timestep
        expr += (
            model.flow[input_levels[flow_level], multiplexer_bus, timestep]
            * model.timeincrement[timestep]
        )

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_input_constraints",
        po.Constraint(level_indices, rule=constrain_input_flows),
    )

    # Helper mapping the levels to the output components
    output_energy = {low: upp - low for low, upp in zip(levels[:-1], levels[1:])}

    # Define constraints on the input flows
    def constrain_output_flows(model, flow_level, timestep):
        expr = 0

        # Energy of the interval above the flow level
        expr -= sum(weights[level, timestep] for level in levels if level > flow_level)
        expr *= output_energy.get(flow_level, 0)

        # Energy which is extracted in this timestep
        expr += (
            model.flow[multiplexer_bus, output_levels[flow_level], timestep]
            * model.timeincrement[timestep]
        )

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_output_constraints",
        po.Constraint(level_indices, rule=constrain_output_flows),
    )

    return
