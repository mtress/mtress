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
    multiplexer_component: Bus,
    input_nodes: dict[Node: float],
    output_nodes: dict[Node: float],
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
    input_nodes : dictionary with oemof.solph.Bus as keys and float as values
        Dictionary of buses which act as inputs and corresponding levels
    output_nodes : dictionary with oemof.solph.Bus as keys and float as values
        Dictionary of buses which act as outputs and corresponding level

    Note that all flows effected by this constraint will be <= 1.
    
    Verbose description can be found in https://arxiv.org/abs/2211.14080
    """

    def _outputs():
        OUTPUTS = po.Set(
            initialize=output_nodes.keys()
        )
        setattr(model, f"{name}_OUTPUTS", OUTPUTS)

        active_output = po.Var(
            OUTPUTS,
            model.TIMESTEPS,
            domain=po.Binary,
            bounds=(0, 1)
        )
        setattr(model, f"{name}_active_output", active_output)

        constraint_name = f"{name}_output_active_constraint"
        def _output_active_rule(model):
            for t in model.TIMESTEPS:
                for o in output_nodes:
                    getattr(model, constraint_name).add(
                        (o, t),
                        model.GenericStorageBlock.storage_content[storage_component, t]
                        >= active_output[o, t]
                        * output_nodes[o]
                        * storage_component.nominal_storage_capacity
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
            constraint_name +"build",
            po.BuildAction(rule=_output_active_rule),
        )

        # Define constraints on the output flows
        def _constraint_output_rule(model, output, timestep):
            return (
                model.flow[multiplexer_component, output, timestep]
                <= active_output[output, timestep]
            )

        setattr(
            model,
            f"{name}_output_constraint",
            po.Constraint(OUTPUTS, model.TIMESTEPS, rule=_constraint_output_rule),
        )
    
    _outputs()

    def _inputs():
        INPUTS = po.Set(
            initialize=input_nodes.keys()
        )
        setattr(model, f"{name}_INPUTS", INPUTS)
        
        active_input = po.Var(
            INPUTS,
            model.TIMESTEPS,
            domain=po.Binary,
            bounds=(0, 1)
        )
        setattr(model, f"{name}_active_input", active_input)

        constraint_name = f"{name}_input_active_constraint"
        def _input_active_rule(model):
            for t in model.TIMESTEPS:
                for o in input_nodes:
                    getattr(model, constraint_name).add(
                        (o, t),
                        model.GenericStorageBlock.storage_content[storage_component, t]
                        / storage_component.nominal_storage_capacity
                        - input_nodes[o]
                        >= 1 - active_input[o, t]
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
            constraint_name +"build",
            po.BuildAction(rule=_input_active_rule),
        )

        # Define constraints on the input flows
        def _constraint_input_rule(model, input, timestep):
            return (
                model.flow[input, multiplexer_component, timestep]
                >= active_input[input, timestep]
            )

        setattr(
            model,
            f"{name}_input_constraint",
            po.Constraint(INPUTS, model.TIMESTEPS, rule=_constraint_input_rule),
        )
    
    _inputs()

    return
