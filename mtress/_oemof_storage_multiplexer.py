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
    intervals = {
        f"interval_{i:02d}": (lower, upper)
        for i, (lower, upper) in enumerate(zip(levels[:-1], levels[1:]))
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

    # Storage content variable for each interval, which is non-zero iff. the storage
    # content lies in the respective interval
    storage_content = po.Var(interval_indices, domain=po.Reals)
    setattr(model, f"{name}_storage_content", storage_content)

    def init_upper_bound_constraints(_, interval, timestep):
        _, upper_bound = intervals[interval]

        expr = 0
        expr += storage_content[interval, timestep]
        expr -= active_interval[interval, timestep] * upper_bound

        return expr <= 0

    setattr(
        model,
        f"{name}_upper_bound_constraints",
        po.Constraint(interval_indices, rule=init_upper_bound_constraints),
    )

    def init_lower_bound_constraints(_, interval, timestep):
        lower_bound, _ = intervals[interval]

        expr = 0
        expr += storage_content[interval, timestep]
        expr -= active_interval[interval, timestep] * lower_bound

        return 0 <= expr

    setattr(
        model,
        f"{name}_lower_bound_constraints",
        po.Constraint(interval_indices, rule=init_lower_bound_constraints),
    )

    def init_storage_content_equality_constraints(_, timestep):
        expr = 0

        for interval in intervals:
            expr += storage_content[interval, timestep]

        expr -= model.GenericStorageBlock.storage_content[storage_component, timestep]
        return expr == 0

    setattr(
        model,
        f"{name}_equality_constraints",
        po.Constraint(model.TIMESTEPS, rule=init_storage_content_equality_constraints),
    )

    # Set for indexing the levels variables
    # def init_level_indices(model):
    #     return [(level, timestep) for timestep in model.TIMESTEPS for level in levels]

    # level_indices = po.Set(dimen=2, ordered=True, initialize=init_level_indices)
    # setattr(model, f"{name}_level_indices", level_indices)

    # Now we can constrain the input and output flows
    # Helper mapping the levels to the input components
    input_map = {
        level: component for (level, component) in zip(levels, input_level_components)
    }

    def constrain_lowest_level(model, timestep):
        lowest_level_component, *_ = input_level_components

        expr = model.flow[lowest_level_component, multiplexer_component, timestep]
        return expr <= 0

    setattr(
        model,
        f"{name}_lowest_level_flow",
        po.Constraint(model.TIMESTEPS, rule=constrain_lowest_level),
    )

    def constrain_input_flows(model, interval, timestep):
        lower_bound, upper_bound = intervals[interval]
        lower_intervals = {
            i: (lo, up) for i, (lo, up) in intervals.items() if lo <= lower_bound
        }

        bound = 0
        bound += upper_bound
        for interval in lower_intervals:
            bound -= storage_content[interval, timestep]

        expr = model.flow[input_map[upper_bound], multiplexer_component, timestep]
        expr -= bound

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_input_constraints",
        po.Constraint(interval_indices, rule=constrain_input_flows),
    )

    # Helper mapping the levels to the output components
    output_map = dict((l, c) for (l, c) in zip(levels, output_level_components))

    def constrain_output_flows(model, interval, timestep):
        lower_bound, upper_bound = intervals[interval]
        higher_intervals = {
            i: (lo, up) for i, (lo, up) in intervals.items() if up >= upper_bound
        }

        bound = 0
        bound -= lower_bound
        for interval in higher_intervals:
            bound += storage_content[interval, timestep]

        expr = model.flow[multiplexer_component, output_map[lower_bound], timestep]
        expr -= bound

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_input_constraints",
        po.Constraint(interval_indices, rule=constrain_output_flows),
    )
