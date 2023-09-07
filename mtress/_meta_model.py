"""The MTRESS meta model itself."""


from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from ._abstract_component import AbstractComponent
    from ._location import Location


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
    ):
        """Initialize the meta model."""
        if locations is None:
            locations = []
        self._locations = locations

    @classmethod
    def from_config(cls, config: dict):
        """Generate the meta model from a configuration dict."""
        # TODO: Implement me!
        raise NotImplementedError("Not implemented yet")

    def add_location(self, location: Location):
        """Add a new location to the meta model."""
        location.assign_meta_model(self)
        self._locations.append(location)

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
