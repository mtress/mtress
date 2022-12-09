# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

"""A constraint to have one common limit for several components.

SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT

"""

from pprint import pprint

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
    # Set for indexing the weight variables
    def init_level_indices(m):
        return [(ts, level) for ts in m.TIMESTEPS for level in levels]

    level_indices = po.Set(dimen=2, ordered=True, initialize=init_level_indices)
    setattr(model, f"{name}_level_indices", level_indices)

    # Set for indexing the SOS constraint per timestep
    def init_sos_indices(m, ts):  # pylint: disable=unsused-argument
        return [(ts, level) for level in levels]

    sos_indices = po.Set(
        model.TIMESTEPS,
        dimen=2,
        ordered=True,
        initialize=init_sos_indices,
    )
    setattr(model, f"{name}_sos_indices", sos_indices)

    # Variable indicating the active interval
    weights = po.Var(level_indices, bounds=(0, 1))
    setattr(model, f"{name}_weights", weights)

    # Allow only two weigths per timestep to be positive
    setattr(
        model,
        f"{name}_sos_constraint",
        po.SOSConstraint(
            model.TIMESTEPS,
            var=weights,
            index=sos_indices,
            sos=2,
        ),
    )

    # Couple the weigths (i.e. the active level) with the storage content, i.e.
    #   levels[n] * weights[n] + levels[n+1] * weights[n+1] == storage_content
    # With the SOS2 constraint above this means
    #     weigths[n] > 0 and weigths[n+1] > 0
    # only if
    #     levels[n] <= storage_content <= levels[n+1]
    def couple_levels_with_storage(model, ts):
        expr = 0
        for l, u in zip(levels[:-1], levels[1:]):
            expr += weights[ts, l] * l + weights[ts, u] * u

        expr -= model.GenericStorageBlock.storage_content[storage_component, ts]
        return expr == 0

    setattr(
        model,
        f"{name}_weights_coupling",
        po.Constraint(model.TIMESTEPS, rule=couple_levels_with_storage),
    )

    # Helper mapping the levels to the input components
    input_map = dict((l, c) for (l, c) in zip(levels, input_level_components))

    # Define constraints on the input flows
    def constrain_input_flows(m, ts, fl):
        expr = 0

        # Iterate over all levels lower that the input flows level
        for l in [l for l in levels if l < fl]:
            expr -= weights[ts, l]

        # TODO: multiply with energy per level interval
        # TODO: multiply with timedelta

        expr += m.flow[input_map[fl], multiplexer_component, ts]

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
    def constrain_output_flows(m, ts, fl):
        expr = 0

        # Iterate over all levels lower that the output flows level
        for l in [l for l in levels if l > fl]:
            expr -= weights[ts, l]

        # TODO: multiply with energy per level interval
        # TODO: multiply with timedelta

        expr += m.flow[multiplexer_component, output_map[fl], ts]

        return expr <= 0

    # Create constraints
    setattr(
        model,
        f"{name}_output_constraints",
        po.Constraint(level_indices, rule=constrain_output_flows),
    )
