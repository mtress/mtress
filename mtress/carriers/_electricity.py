"""Electricity energy carrier."""

from oemof import solph

from ._abstract_carrier import AbstractCarrier


class Electricity(AbstractCarrier):
    """
    Functionality: Electricity connections at a location. This class
        represents a local electricity grid with or without connection
        to the global electricity grid.

        All default busses, sources and sinks are automatically generated
        and interconnected when the carrier is initialized. Automatically
        generated are the following: one bus each for production, distribution,
        export, grid_in (actual grid supply with costs), grid_out (external
        market to sell electricity to) as well as a source (additional
        unidirictional grid connection) and a sink (export).

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    Procedure: Create a simple electricity carrier by doing the following
        and adding costs to the grid supply.
    TODO: the term demand_rate feels really unintuitive --> better variable_name for that?

            house_1.add_carrier(
                carriers.Electricity(costs={"working_price": 35, "demand_rate": 0})

    Notice: Costs of the grid supply (working_price and demand_rate) need to
        be specified.

    """

    def __init__(self, grid_connection=True, **kwargs):
        """Initialize electricity carrier."""
        super().__init__(**kwargs)
        self._grid_connection = grid_connection

    def build(self):
        self.production = None
        self.distribution = None
        self.grid_connection = self._grid_connection

        self.distribution = b_dist = solph.Bus(
            label=self._generate_label("dist")
        )
        self.production = b_prod = solph.Bus(
            label=self._generate_label("prod"),
            outputs={b_dist: solph.Flow()},
        )
        self.location.add_carrier(self)

        b_export = solph.Bus(label=self._generate_label("b_export"))
        b_grid = solph.Bus(label=self._generate_label("b_grid"))

        self.location.energy_system.add(b_dist, b_prod, b_export, b_grid)

        # (unidirectional) grid connection
        # RLM customer for district and larger buildings
        s_import = solph.Source(
            label=self._generate_label("s_import"),
            outputs={b_grid: solph.Flow()},
        )
        self.location.energy_system.add(s_import)
        # TODO: Categorize import flow

        b_grid_in = solph.Bus(
            label=self._generate_label("grid_in"),
            inputs={
                b_grid: solph.Flow(
                    variable_costs=self.costs["working_price"],
                    investment=solph.Investment(
                        ep_costs=self.costs["demand_rate"]
                    ),
                )
            },
            outputs={
                b_dist: solph.Flow()
            },
        )

        # create external market to sell electricity to
        b_grid_out = solph.Bus(
            label=self._generate_label("grid_out"),
            inputs={
                b_export: solph.Flow()
            },
        )

        self.location.energy_system.add(b_grid_in, b_grid_out)

        d_out = solph.Sink(
            self._generate_label("export"),
            inputs={b_grid_out: solph.Flow()},
        )
        self.location.energy_system.add(d_out)

        # TODO: categorize out flow
