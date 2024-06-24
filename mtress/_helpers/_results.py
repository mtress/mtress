"""Utility functions for the analysis of solph results."""


def get_flows(results):
    """
    Extract flows from results dictionary.

    :param results: Results from solph optimization
    """
    flows = {
        (source_node.label, destination_node.label): result["sequences"]["flow"]
        for (source_node, destination_node), result in results.items()
        if destination_node is not None and not source_node == destination_node
    }

    return flows


def get_status(results):
    """
    Extract status of flows from results dictionary.

    :param results: Results from solph optimization
    """
    flows = {
        (source_node.label, destination_node.label): result["sequences"]["status"]
        for (source_node, destination_node), result in results.items()
        if destination_node is not None
        and "status" in result["sequences"]
        and not source_node == destination_node
    }

    return flows


def get_variables(results):
    """
    Extract variables from results dictionary.

    To access the data you might want to use the xs function, i.e.
    >>> flows = get_flows(results)
    >>> flows.xs('component0', axis=1, level='component')
    >>> flows.xs('variable0', axis=1, level='variable_name')

    :param results: Results from oemof optimization
    """
    variables = {
        source_node.label: result["sequences"]
        for (source_node, destination_node), result in results.items()
        if destination_node is None
    }

    return variables
