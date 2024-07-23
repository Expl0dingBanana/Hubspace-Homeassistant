import logging
import json

import os
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HubSpaceConfigEntry
from .anonomyize_data import generate_anon_data
from hubspace_async import HubSpaceConnection
from .coordinator import HubSpaceDataUpdateCoordinator

logger = logging.getLogger(__name__)


class HubSpaceDiagnostics(ButtonEntity):
    """A button that enables easy debug!

    :ivar _name: Name of the device
    :ivar _hs: HubSpace connector
    """

    def __init__(
        self,
        hs: HubSpaceConnection,
    ) -> None:
        self._name = "Diagnostic button"
        self._hs = hs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        pass


    async def async_press(self) -> None:
        """Handle the button press."""
        await self._hs.populate_data()
        data = generate_anon_data(self._hs)
        logger.debug("CWD: %s", os.getcwd())
        with open("hubspace_data.json", "w") as fh:
            json.dump(data, fh, indent=4)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HubSpaceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Fan entities from a config_entry."""
    coordinator_hubspace: HubSpaceDataUpdateCoordinator = (
        entry.runtime_data.coordinator_hubspace
    )
    hub_entity = HubSpaceDiagnostics(coordinator_hubspace.conn)
    async_add_entities([hub_entity])
