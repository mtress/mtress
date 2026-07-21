"""Utility functions for the analysis of solph results."""


def get_flow_units(solph_model):
    units = {}
    flows = solph_model.model.flows
    for k, v in flows.items():
        units[k] = v.custom_properties.get("unit", "")
    return units


def get_energy_types(solph_model):
    colours = {}
    flows = solph_model.model.flows
    for k, v in flows.items():
        colours[k] = v.custom_properties.get("energy_type", "")
    return colours


def get_storage_content(results):
    """
    Extract storage content from results dictionary.

    :param results: Results from solph optimization
    """
    storage_content = {
        source_node.label: result["sequences"]["storage_content"]
        for (source_node, destination_node), result in results.items()
        if "storage_content" in result["sequences"]
    }

    return storage_content


def get_status(results):
    """
    Extract status of flows from results dictionary.

    :param results: Results from solph optimization
    """
    flows = {
        (source_node.label, destination_node.label): result["sequences"][
            "status"
        ]
        for (source_node, destination_node), result in results.items()
        if destination_node is not None
        and "status" in result["sequences"]
        and not source_node == destination_node
    }

    return flows


def get_variables(results):
    """
    Extract variables from results dictionary.

    :param results: Results from oemof optimization
    """
    # To access the data you might want to use the xs function, i.e.
    # >>> flows = get_flows(results)
    # >>> flows.xs('component0', axis=1, level='component')
    # >>> flows.xs('variable0', axis=1, level='variable_name')
    variables = {
        source_node.label: result["sequences"]
        for (source_node, destination_node), result in results.items()
        if destination_node is None
    }

    return variables
