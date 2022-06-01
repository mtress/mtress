"""Electricity energy carrier."""

from oemof import solph

from ._abstract_energy_carrier import AbstractEnergyCarrier

class Electricity(AbstractEnergyCarrier):
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

        self.distribution = b_dist = solph.Bus(label=self._generate_label(solph.Bus, "dist"))
        self.production = b_prod = solph.Bus(
            label=self._generate_label(solph.Bus, "prod"),
            outputs={b_dist: solph.Flow()}
        )

        b_export = solph.Bus(label=self._generate_label(solph.Bus, "export"))
        b_grid = solph.Bus(label=self._generate_label(solph.Bus, "grid"))

        self._energy_system.add(b_dist, b_prod, b_export, b_grid)

        # (unidirectional) grid connection
        # RLM customer for district and larger buildings
        s_import = solph.Source(label="m_el_in", outputs={b_grid: solph.Flow()})
        self._energy_system.add(s_import)
        # TODO: Categorize import flow

        costs = {"working_price": 0, "demand_rate": 0}
        # self._location.costs

        b_grid_in = solph.Bus(
            label=self._generate_label(solph.Bus, "grid_in"),
            inputs={
                b_grid: solph.Flow(
                    variable_costs=costs["working_price"],
                    investment=solph.Investment(
                        ep_costs=costs["demand_rate"]
                    ),
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
            label=self._generate_label(solph.Bus, "grid_out"),
            inputs={
                b_export: solph.Flow(
                    nonconvex=solph.NonConvex(), nominal_value=1e5, grid_connection=True
                )
            },
        )

        self._energy_system.add(b_grid_in, b_grid_out)

        d_out = solph.Sink(self._generate_label(solph.Sink, "export"), inputs={b_grid_out: solph.Flow()})
        self._energy_system.add(d_out)

        # TODO: categorize out flow
