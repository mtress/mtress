import pandas as pd
from oemof.solph import Bus, EnergySystem, Flow, Model
from oemof.solph.components import GenericStorage, Source, Sink
from oemof.solph.processing import results

import matplotlib.pyplot as plt

from mtress._storage_level_constraint import storage_level_constraint


es = EnergySystem(
    timeindex=pd.date_range("2022-01-01", freq="60T", periods=16),
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

in_1 = Source(
    label="in_1",
    outputs={multiplexer: Flow(nominal_value=0.1)}
)
es.add(in_1)

out_0 = Sink(
    label="out_0",
    inputs={multiplexer: Flow(nominal_value=0.25, variable_costs=-0.1)}
)
es.add(out_0)

out_1 = Sink(
    label="out_1",
    inputs={multiplexer: Flow(nominal_value=0.15, variable_costs=-0.1)}
)
es.add(out_1)


model = Model(es)

storage_level_constraint(
    model=model,
    name="multiplexer",
    storage_component=storage,
    multiplexer_bus=multiplexer,
    input_levels={in_1: 1/3},
    output_levels={out_0: 0.1, out_1: 1/2},
)
model.solve()

my_results = results(model)

df = pd.DataFrame(my_results[(storage, None)]["sequences"])
df["out_status"] = my_results[(out_1, None)]["sequences"]
df["in_status"] = 1 - my_results[(in_1, None)]["sequences"]

df["in1"] = my_results[(in_1, multiplexer)]["sequences"]
df["out0"] = my_results[(multiplexer, out_0)]["sequences"]
df["out1"] = my_results[(multiplexer, out_1)]["sequences"]

plt.step(df.index, df["in1"], where="post", label="inflow (<1/3)")
plt.step(df.index, df["out0"], where="post", label="outflow (>0.1)")
plt.step(df.index, df["out1"], where="post", label="outflow (>0.5)")

plt.grid()
plt.legend()

plt.twinx()

plt.plot(df.index, df["storage_content"], "r-", label="storage content")
plt.ylim(0, 3)
plt.legend(loc="center right")

print(df)

plt.show()

