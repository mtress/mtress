"""The MTRESS meta model itself."""

from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from ._abstract_component import AbstractComponent
    from mtress.technologies.grid_connection._abstract_grid_connection import AbstractGridConnection

from ._location import Location


@dataclass
class Connection:
    """Class for keeping track of an item in inventory."""

    source: Location
    destination: Location
    carrier: type


class MetaModel:
    """
    Meta model of the energy system.

    Functionality: A meta model acts as a container for the model.
    It contains global information, such as the time / a timeseries,
    as well as defaults which can be overwritten for specific
    locations (e.g. weather data). Once the energy system is about
    to be solved, it makes sureevery location has all the needed
    connections and constraints set.

    Procedure: Create a (basic) meta model by doing the following:
        meta_model = MetaModel()

    Further procedure is described in the location class.
    """

    def __init__(
        self,
        locations: List[Location] = None,
        connections: List[(Location, Location, AbstractGridConnection)] = None,
    ):
        """Initialize the meta model."""
        if connections is None:
            connections = []
        if locations is None:
            locations = []

        self._connections = connections
        self._locations = locations

    @classmethod
    def from_config(cls, config: dict):
        """Generate the meta model from a configuration dict."""
        # TODO: Implement me!
        raise NotImplementedError("Not implemented yet")

    def add_connection(self, connection: Connection):
        """Connect two locations in the meta model."""
        if (
            connection.source in self._locations
            and connection.destination in self._locations
        ):
            self._connections.append(connection)
        else:
            raise ValueError(
                "At least one loacation to be connected is not known to the model."
            )

    def add_location(self, location: Location):
        """Add a new location to the meta model."""
        self._locations.append(location)

    def add(self, entity: Connection | Location) -> None:
        """Convenience function to add something."""
        match entity:
            case Connection():
                self.add_connection(entity)
            case Location():
                self.add_location(entity)
            case _:
                raise ValueError(
                    "Object to be added is of type that cannot be handled."
                )

    @property
    def connections(self) -> Iterable[Connection]:
        """Iterate over all connections."""
        for connection in self._connections:
            yield connection

    @property
    def locations(self) -> Iterable[Location]:
        """Iterate over all locations."""
        for location in self._locations:
            yield location

    @property
    def components(self) -> Iterable[AbstractComponent]:
        """Iterate over all components of all locations."""
        for location in self.locations:
            for component in location.components:
                yield component
