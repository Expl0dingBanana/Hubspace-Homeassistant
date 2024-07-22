"""The HubSpace coordinator."""

import logging
from asyncio import timeout
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from hubspace_async import HubSpaceConnection, HubSpaceDevice, HubSpaceState

from . import discovery

_LOGGER = logging.getLogger(__name__)


class HubSpaceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        conn: HubSpaceConnection,
        friendly_names: list[str],
        room_names: list[str],
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.conn = conn
        self.tracked_devices: list[HubSpaceDevice] = []
        self.states: dict[str, list[HubSpaceState]] = {}
        self.friendly_names = friendly_names
        self.room_names = room_names

        super().__init__(
            hass,
            _LOGGER,
            name="hubspace",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            async with timeout(10):
                await self.conn.populate_data()
        except Exception as error:
            raise UpdateFailed(error) from error
        self.tracked_devs = await discovery.get_requested_devices(
            self.conn, self.friendly_names, self.room_names
        )
        for device in self.tracked_devs:
            child_id = device.id
            self.states[child_id] = await self.conn.get_device_state(child_id)
        return {
            "devices": self.tracked_devs,
            "states": self.states,
        }
