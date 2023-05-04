"""A constraint to allow flows from to a storage based on the storage level.

SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof.network.network import Node
from oemof.solph import Bus, Model
from oemof.solph.components import GenericStorage
from pyomo import environ as po


def storage_level_constraint(
    model: Model,
    name: str,
    storage_component: GenericStorage,
    multiplexer_bus: Bus,
    inputs: dict[float, Node] = None,
    outputs: dict[float, Node] = None,
):
    r"""
    Add constraints to implement storage content based access.

    Parameters
    ----------
    model : oemof.solph.Model
        Model to which the constraint is added.
    name : string
        Name of the multiplexer.
    storage_component : oemof.solph.components.GenericStorage
        Storage component whose content should mandate the possible inputs and outputs.
    multiplexer_bus : oemof.solph.Bus
        Bus which connects the input and output levels to the storage.
    inputs : dictionary with float as keys and oemof.solph.Bus as values
        Dictionary of buses which act as inputs and corresponding levels
    outputs : dictionary with float as keys and oemof.solph.Bus as values
        Dictionary of buses which act as outputs and corresponding level

    Note that all flows effected by this constraint will be <= 1.

    Verbose description can be found in https://arxiv.org/abs/2211.14080
    """
    if inputs is None:
        inputs = {}

    if outputs is None:
        outputs = {}

    def _outputs():
        OUTPUTS = po.Set(initialize=outputs.values())
        setattr(model, f"{name}_OUTPUTS", OUTPUTS)

        active_output = po.Var(
            OUTPUTS, model.TIMESTEPS, domain=po.Binary, bounds=(0, 1)
        )
        setattr(model, f"{name}_active_output", active_output)

        constraint_name = f"{name}_output_active_constraint"

        def _output_active_rule(m):
            for t in m.TIMESTEPS:
                for level, node in outputs.items():
                    getattr(m, constraint_name).add(
                        (node, t),
                        m.GenericStorageBlock.storage_content[storage_component, t + 1]
                        >= active_output[node, t]
                        * level
                        * storage_component.nominal_storage_capacity,
                    )

        setattr(
            model,
            constraint_name,
            po.Constraint(
                OUTPUTS,
                model.TIMESTEPS,
                noruleinit=True,
            ),
        )
        setattr(
            model,
            constraint_name + "build",
            po.BuildAction(rule=_output_active_rule),
        )

        # Define constraints on the output flows
        def _constraint_output_rule(m, o, t):
            return m.flow[multiplexer_bus, o, t] <= active_output[o, t]

        setattr(
            model,
            f"{name}_output_constraint",
            po.Constraint(OUTPUTS, model.TIMESTEPS, rule=_constraint_output_rule),
        )

    _outputs()

    def _inputs():
        INPUTS = po.Set(initialize=inputs.values())
        setattr(model, f"{name}_INPUTS", INPUTS)

        inactive_input = po.Var(
            INPUTS, model.TIMESTEPS, domain=po.Binary, bounds=(0, 1)
        )
        setattr(model, f"{name}_active_input", inactive_input)

        constraint_name = f"{name}_input_active_constraint"

        def _input_active_rule(m):
            for t in m.TIMESTEPS:
                for level, node in inputs.items():
                    getattr(m, constraint_name).add(
                        (node, t),
                        m.GenericStorageBlock.storage_content[storage_component, t]
                        / storage_component.nominal_storage_capacity
                        - level
                        <= inactive_input[node, t],
                    )

        setattr(
            model,
            constraint_name,
            po.Constraint(
                INPUTS,
                model.TIMESTEPS,
                noruleinit=True,
            ),
        )
        setattr(
            model,
            constraint_name + "build",
            po.BuildAction(rule=_input_active_rule),
        )

        # Define constraints on the input flows
        def _constraint_input_rule(m, i, t):
            return m.flow[i, multiplexer_bus, t] <= 1 - inactive_input[i, t]

        setattr(
            model,
            f"{name}_input_constraint",
            po.Constraint(INPUTS, model.TIMESTEPS, rule=_constraint_input_rule),
        )

    _inputs()

    return
