"""Electricity energy carrier."""

from oemof import solph

from ._abstract_carrier import AbstractCarrier


class Electricity(AbstractCarrier):
    """
    Electricity connections at a location.

    This class represents a local electricity grid with or without connection
    to the global electricity grid.
    """

    def __init__(self, grid_connection=True, **kwargs):
        """Prepare electricity energy carrier and add solph components to the energy system."""
        super().__init__(**kwargs)

        self.production = None
        self.distribution = None
        self.grid_connection = grid_connection

        self.distribution = b_dist = solph.Bus(label=self._generate_label("dist"))
        self.production = b_prod = solph.Bus(
            label=self._generate_label("prod"),
            outputs={b_dist: solph.Flow()},
        )

        b_export = solph.Bus(label=self._generate_label("export"))
        b_grid = solph.Bus(label=self._generate_label("grid"))

        self.location.energy_system.add(b_dist, b_prod, b_export, b_grid)

        # (unidirectional) grid connection
        # RLM customer for district and larger buildings
        s_import = solph.Source(
            label=self._generate_label("grid_in"), outputs={b_grid: solph.Flow()}
        )
        self.location.energy_system.add(s_import)
        # TODO: Categorize import flow

        costs = {"working_price": 0, "demand_rate": 0}
        # self._location.costs

        b_grid_in = solph.Bus(
            label=self._generate_label("grid_in"),
            inputs={
                b_grid: solph.Flow(
                    variable_costs=costs["working_price"],
                    investment=solph.Investment(ep_costs=costs["demand_rate"]),
                )
            },
            outputs={
                b_dist: solph.Flow(
                    nonconvex=solph.NonConvex(), nominal_value=1e5, grid_connection=True
                )
            },
        )

        # create external market to sell electricity to
        b_grid_out = solph.Bus(
            label=self._generate_label("grid_out"),
            inputs={
                b_export: solph.Flow(
                    nonconvex=solph.NonConvex(), nominal_value=1e5, grid_connection=True
                )
            },
        )

        self.location.energy_system.add(b_grid_in, b_grid_out)

        d_out = solph.Sink(
            self._generate_label("export"),
            inputs={b_grid_out: solph.Flow()},
        )
        self.location.energy_system.add(d_out)

        # TODO: categorize out flow
