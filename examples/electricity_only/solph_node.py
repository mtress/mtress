"""
Basic working 'electricity only' example.

Basic working 'electricity only' example which includes a location (house),
an electricity carrier which acts as a electricity source/supply from the
official grid (working price of 35 and 45 ct/kWh for two time steps,
respectively) as well as a demand (consumer) with a demand time series.

At first an energy system (here meta_model) is defined with a time series
(index). Afterwards a location is defined and added to the energysystem.
Then the electricity carrier and demand (time series) are added to the
energysystem.

The core of this example is adding a solph node (GernericStorage) to the
existing MTRESS model.

Finally, the energy system is optimised/solved via
solph_representation.solve(). Not that graph plotting currently does not
support this way of modelling.
"""

import os

from oemof import solph

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))
meta_model = MetaModel()

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=[35, 45]))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0, 0.5],
    )
)

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

carrier_node = solph_representation.energy_system.node[
    ("house_1", "ElectricityCarrier", "distribution")
]

solph_representation.energy_system.add(
    solph.components.GenericStorage(
        label="vanilla_solph_storage",
        inputs={carrier_node: solph.Flow()},
        outputs={carrier_node: solph.Flow()},
        nominal_storage_capacity=0.75,
    )
)

# Build the solph model after adding stuff to the solph energy system.
# Otherwise, they will be ignored as the model is already built.
solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

print(
    flows[
        ("house_1", "ElectricityGridConnection", "source_import"),
        ("house_1", "ElectricityGridConnection", "grid_import"),
    ]
)

print(
    flows[
        ("house_1", "ElectricityCarrier", "distribution"),
        ("vanilla_solph_storage"),
    ]
)

print(
    flows[
        ("house_1", "electricity demand", "input"),
        ("house_1", "electricity demand", "sink"),
    ]
)

solph_representation.graph(flow_results=flows)
