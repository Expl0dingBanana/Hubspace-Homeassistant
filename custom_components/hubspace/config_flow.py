"""Config flow for HubSpace integration."""

from __future__ import annotations

import logging
from asyncio import timeout
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from hubspace_async import HubSpaceConnection

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

        if user_input is not None:
            try:
                async with timeout(10):
                    conn = HubSpaceConnection(
                        user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    )
                    await conn.get_account_id()
            except TimeoutError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["unknown"] = "generic"
            else:
                await self.async_set_unique_id(
                    await conn.account_id, raise_on_progress=False
                )

                return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=PLATFORM_SCHEMA,
            errors=errors,
        )
