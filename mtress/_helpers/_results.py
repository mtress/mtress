"""Utility functions for the analysis of oemof results."""

import pandas as pd


def get_flows(results):
    """
    Extract flows from results dictionary.

    To access the data you might want to use the xs function, i.e.
    >>> flows = get_flows(results)
    >>> flows.xs('component0', axis=1, level='source')
    >>> flows.xs('component0', axis=1, level='destination')

    :param results: Results from oemof optimization
    """
    flows = {
        (source_node.label, destination_node.label): result["sequences"]["flow"]
        for (source_node, destination_node), result in results.items()
        if destination_node is not None and not source_node == destination_node
    }

    return pd.concat(
        flows.values(), axis=1, names=["source", "destination"], keys=flows.keys()
    )


def get_status(results):
    """
    Extract status of flows from results dictionary.

    To access the data you might want to use the xs function, i.e.
    >>> flows = get_flows(results)
    >>> flows.xs('component0', axis=1, level='source')
    >>> flows.xs('component0', axis=1, level='destination')

    :param results: Results from oemof optimization
    """
    flows = {
        (source_node.label, destination_node.label): result["sequences"]["status"]
        for (source_node, destination_node), result in results.items()
        if destination_node is not None
        and "status" in result["sequences"]
        and not source_node == destination_node
    }

    return pd.concat(
        flows.values(), axis=1, names=["source", "destination"], keys=flows.keys()
    )


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

    return pd.concat(
        variables.values(),
        axis=1,
        names=[
            "component",
        ],
        keys=variables.keys(),
    )


def get_flows_for_component(flows, component):
    """Get flows in and out of component."""
    inflows = (
        flows.xs(component, axis=1, level="destination")
        if component in flows.columns.get_level_values("destination")
        else pd.DataFrame(index=flows.index)
    )

    outflows = (
        flows.xs(component, axis=1, level="source")
        if component in flows.columns.get_level_values("source")
        else pd.DataFrame(index=flows.index)
    )

    return pd.concat(
        [
            inflows.rename("from_{0}".format, axis=1),
            outflows.rename("to_{0}".format, axis=1),
        ],
        axis=1,
    )
