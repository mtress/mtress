# Model Template for Residential Energy Supply Systems (MTRESS)

This is a generic model for [oemof.solph](https://github.com/oemof/oemof-solph/)
that provides a variety of possible technology combinations for energy supply systems.
It is tailored for optimising control strategies fulfilling fixed demand time series
for electricity, heat, and domestic hot water using any selected combination
of the implemented supply technologies.

The development was partly funded by the Federal Ministry for Economic Affairs and Energy (BMWi)
and the Federal Ministry of Education and Research (BMBF) of Germany
in the project ENaQ (project number 03SBE111).


## Installation

MTRESS depends on solph, which is automatically instaled using pip
if you `pip-install mtress`. However, pip will not install a solver,
to perform the actual optimisation. Please refer to the
[https://oemof-solph.readthedocs.io/en/v0.4.4/readme.html#installing-a-solver](documentation of solph)
to learn how to install a solver.
