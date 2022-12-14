# -*- coding: utf-8 -*-

"""A constraint to have one common limit for several components.

SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT

"""


from oemof.solph import Bus, Model
from oemof.solph.components import GenericStorage
from pyomo import environ as po


def storage_multiplexer_constraint(
    model: Model,
    name: str,
    storage_component: GenericStorage,
    multiplexer_component: Bus,
    input_level_components: list[Bus],
    output_level_components: list[Bus],
    levels: list[float],
):
    r"""
    Add constraits to implement a storage content dependent multiplexer.

    Adds a constraint to the given model that restricts
    the weighted sum of variables to a corridor.

    **The following constraints are build:**

      .. math::
        l_\mathrm{low} \le \sum v_i(t) \times w_i(t) \le l_\mathrm{up}
        \forall t

    Parameters
    ----------
    model : oemof.solph.Model
        Model to which the constraint is added.
    limit_name : string
        Name of the constraint to create
    quantity : pyomo.core.base.var.IndexedVar
        Shared Pyomo variable for all components of a type.
    components : list of components
        list of components of the same type
    weights : list of numeric values
        has to have the same length as the list of components
    lower_limit : numeric
        the lower limit
    upper_limit : numeric
        the lower limit

    Examples
    --------
    The constraint can e.g. be used to define a common storage
    that is shared between parties but that do not exchange
    energy on balance sheet.
    Thus, every party has their own bus and storage, respectively,
    to model the energy flow. However, as the physical storage is shared,
    it has a common limit.

    >>> import pandas as pd
    >>> from oemof import solph
    >>> date_time_index = pd.date_range('1/1/2012', periods=5, freq='H')
    >>> energysystem = solph.EnergySystem(timeindex=date_time_index)
    >>> b1 = solph.buses.Bus(label="Party1Bus")
    >>> b2 = solph.buses.Bus(label="Party2Bus")
    >>> storage1 = solph.components.GenericStorage(
    ...     label="Party1Storage",
    ...     nominal_storage_capacity=5,
    ...     inputs={b1: solph.flows.Flow()},
    ...     outputs={b1: solph.flows.Flow()})
    >>> storage2 = solph.components.GenericStorage(
    ...     label="Party2Storage",
    ...     nominal_storage_capacity=5,
    ...     inputs={b1: solph.flows.Flow()},
    ...     outputs={b1: solph.flows.Flow()})
    >>> energysystem.add(b1, b2, storage1, storage2)
    >>> components = [storage1, storage2]
    >>> model = solph.Model(energysystem)
    >>> solph.constraints.shared_limit(
    ...    model,
    ...    model.GenericStorageBlock.storage_content,
    ...    "limit_storage", components,
    ...    [1, 1], upper_limit=5)
    """
    # http://yetanothermathprogrammingconsultant.blogspot.com/2015/10/piecewise-linear-functions-in-mip-models.html
    # Helper mapping
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
    input_map = dict((l, c) for (l, c) in zip(levels, input_level_components))

    # Define constraints on the input flows
    def constrain_input_flows(model, flow_level, timesteps):
        expr = 0
        expr -= sum(weights[level, timesteps] for level in levels if level < flow_level)

        # TODO: multiply with energy per level interval
        # TODO: multiply with timedelta

        expr += model.flow[input_map[flow_level], multiplexer_component, timesteps]

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_input_constraints",
        po.Constraint(level_indices, rule=constrain_input_flows),
    )

    # Helper mapping the levels to the output components
    output_map = dict((l, c) for (l, c) in zip(levels, output_level_components))

    # Define constraints on the input flows
    def constrain_output_flows(model, flow_level, timestep):
        expr = 0
        expr -= sum(weights[level, timestep] for level in levels if level > flow_level)

        # TODO: multiply with energy per level interval
        # TODO: multiply with timedelta

        expr += model.flow[multiplexer_component, output_map[flow_level], timestep]

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_output_constraints",
        po.Constraint(level_indices, rule=constrain_output_flows),
    )

    return
