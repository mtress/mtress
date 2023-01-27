import pandas as pd
from oemof.solph import Bus, EnergySystem, Flow, Model
from oemof.solph.components import GenericStorage, Source, Sink
from oemof.solph.processing import results

from mtress._storage_level_constraint import storage_level_constraint


es = EnergySystem(
    timeindex=pd.date_range("2022-01-01", freq="60T", periods=12),
    infer_last_interval=True,
)

multiplexer = Bus(
    label="multiplexer",
)

storage = GenericStorage(
    label="storage",
    nominal_storage_capacity=3,
    initial_storage_level=1,
    balanced=False,
    inputs={multiplexer: Flow()},
    outputs={multiplexer: Flow()},
)

es.add(multiplexer, storage)

out_0 = Sink(
    label="out_0",
    inputs={multiplexer: Flow(nominal_value=0.1, variable_costs=-0.1)}
)
es.add(out_0)

out_1 = Sink(
    label="out_1",
    inputs={multiplexer: Flow(nominal_value=0.1, variable_costs=-0.1)}
)
es.add(out_1)


model = Model(es)

storage_level_constraint(
    model=model,
    name="multiplexer",
    storage_component=storage,
    multiplexer_component=multiplexer,
    input_levels={},
    output_levels={out_0: 0,
                   out_1: 2/3},
)
model.solve()

my_results = results(model)

print(my_results[(storage, None)]["sequences"])
