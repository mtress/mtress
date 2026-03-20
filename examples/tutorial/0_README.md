# Tutorial instructions

## CBC & Graphviz
### CBC solver
For MTRESS to run we need a solver. The default solver is CBC. Of course other solvers can be used as well. Since in it's core, MTRESS is based on `pyomo`, a list of supported solvers can be found here: [supported solvers](https://pyomo.readthedocs.io/en/stable/api/pyomo.solvers.plugins.solvers.html).
For simlicity we can download CBC here: [CBC releases](https://github.com/coin-or/Cbc/releases)

### Visualization with Graphviz
To understand how MTRESS works and builds an energy system, it can be very helpful to inspect the energy system. For this purpopse we rely on Graphviz, which can be downloaded here: [Graphviz download](https://graphviz.org/download/)

### Setting up the PATH (WINDOWS)
Once CBC and Graphviz are downloaded, the packages have to be unpacked (`.zip` files) and stored to a location of your liking. Once thats done, they have to be added to your environmental variables. Edit the `PATH` and add the `bin` folder of the packages.

## MTRESS requirements
Setup a new `venv` or any other environment of your liking and activate. Lastly, install the required python libraries for MTRESS. The easiest way to do so is via: `pip install .`