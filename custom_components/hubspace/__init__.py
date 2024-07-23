"""Hubspace integration."""

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from hubspace_async import HubSpaceConnection

from .const import CONF_FRIENDLYNAMES, CONF_ROOMNAMES, UPDATE_INTERVAL_OBSERVATION
from .coordinator import HubSpaceDataUpdateCoordinator

logger = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN]


@dataclass
class HubSpaceData:
    """Data for HubSpace integration."""

    coordinator_hubspace: HubSpaceDataUpdateCoordinator


type HubSpaceConfigEntry = ConfigEntry[HubSpaceData]


async def async_setup_entry(hass: HomeAssistant, entry: HubSpaceData) -> bool:
    """Set up HubSpace as config entry."""
    conn = HubSpaceConnection(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    coordinator_hubspace = HubSpaceDataUpdateCoordinator(
        hass,
        conn,
        entry.data[CONF_FRIENDLYNAMES],
        entry.data[CONF_ROOMNAMES],
        UPDATE_INTERVAL_OBSERVATION,
    )

    await coordinator_hubspace.async_config_entry_first_refresh()

    entry.runtime_data = HubSpaceData(
        coordinator_hubspace=coordinator_hubspace,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
