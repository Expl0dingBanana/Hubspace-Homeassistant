"""Config flow for HubSpace integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, HANDLERS
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
# from hubspace_async import HubSpaceConnection

from .const import CONF_FRIENDLYNAMES, CONF_ROOMNAMES, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_FRIENDLYNAMES, default=""): str,
        vol.Optional(CONF_ROOMNAMES, default=""): str,
    }
)


@HANDLERS.register(DOMAIN)
class HubSpaceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HubSpace"""

    VERSION = 1
    username: str
    password: str
    friendly_names: str
    room_names: str

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        return self.async_show_form(
            step_id="user",
            data_schema=PLATFORM_SCHEMA,
            errors=errors,
        )
