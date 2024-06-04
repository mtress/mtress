# Model Template for Renewable Energy Supply Systems (MTRESS)

This is a generic model for [oemof.solph](https://github.com/oemof/oemof-solph/)
that provides a variety of possible technology combinations for energy supply systems.
It is tailored for optimising control strategies fulfilling fixed demand time series
for electricity, heat, and domestic hot water using any selected combination
of the implemented supply technologies.

The development of Version 2 was funded by the Federal Ministry for Economic Affairs and Energy (BMWi)
and the Federal Ministry of Education and Research (BMBF) of Germany
in the project ENaQ (project number 03SBE111).
The development of the heat sector formulations in Version 3 was funded by the Federal Ministry of
Education and Research (BMBF) of Germany in the project Wärmewende Nordwest (project number 03SF0624).


## Installation

MTRESS depends on solph, which is automatically instaled using pip
if you `pip install mtress`. However, pip will not install a solver,
to perform the actual optimisation. Please refer to the
[documentation of solph](https://oemof-solph.readthedocs.io/en/v0.4.4/readme.html#installing-a-solver)
to learn how to install a solver.

## Documentation

The auto-generated documentation can be found on the [GitLab pages](https://mtress-ecosystem.pages.gitlab.dlr.de/mtress).


## Contributing

You are welcome to contribute to MTRESS. We use [Black code style](https://black.readthedocs.io/),
and put our code under [MIT license](LICENSE). When contributing, you need to do the same.
For smaller changes, you can just open a merge request. If you plan something bigger,
please open an issue first, so that we can discuss beforehand and avoid double work.


## Contact

The software development is administrated by [Patrik Schönfeldt](mailto:patrik.schoenfeldt@dlr.de),
for general questions please contact him. Individual authors may leave their contact information
in the [citation.cff](CITATION.cff).
