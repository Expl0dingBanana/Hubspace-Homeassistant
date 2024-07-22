"""Platform for light integration."""

from __future__ import annotations

import logging
from datetime import timedelta

# Import exceptions from the requests module
import requests.exceptions
import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_COLOR_TEMP_KELVIN,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall

# Import the device class from the component that you want to support
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import Any, ConfigType, DiscoveryInfoType

from . import CONF_DEBUG, CONF_FRIENDLYNAMES, CONF_ROOMNAMES, hubspace_device
from .hubspace import HubSpace

SCAN_INTERVAL = timedelta(seconds=30)
SERVICE_NAME = "send_command"
_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_DEBUG, default=False): cv.boolean,
        vol.Required(CONF_FRIENDLYNAMES, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Required(CONF_ROOMNAMES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)


def _brightness_to_hass(value):
    if value is None:
        value = 0
    return int(value) * 255 // 100


def _brightness_to_hubspace(value):
    return value * 100 // 255


def _convert_color_temp(value):
    if isinstance(value, str) and value.endswith("K"):
        value = value[:-1]
    if value is None:
        value = 1
    return 1000000 // int(value)


def create_ha_entity(hs: HubSpace, debug: bool, entity: hubspace_device.HubSpaceDevice):
    """Query HubSpace and find devices to add

    :param hs: HubSpace connection
    :param debug: If debug is enabled
    :param entity: HubSpace API device

    """
    if entity.device_class in ["light", "switch"]:
        return HubspaceLight(
            hs,
            entity.friendly_name,
            debug,
            childId=entity.id,
            model=entity.model,
            deviceId=entity.device_id,
            functions=entity.functions,
        )
    else:
        _LOGGER.debug(
            f"Unable to process the entity {entity.friendly_name} of class {entity.device_class}"
        )


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Awesome Light platform."""

    # Assign configuration variables.
    # The configuration check takes care they are present.

    username = config[CONF_USERNAME]
    password = config.get(CONF_PASSWORD)
    debug = config.get(CONF_DEBUG)
    try:
        hs = HubSpace(username, password)
    except requests.exceptions.ReadTimeout as ex:
        # Where does this exception come from? The integration will break either way
        # but more spectacularly since the exception is not imported
        raise PlatformNotReady(
            f"Connection error while connecting to hubspace: {ex}"
        ) from ex

    entities = []
    friendly_names: list[str] = config.get(CONF_FRIENDLYNAMES, [])
    room_names: list[str] = config.get(CONF_ROOMNAMES, [])
    data = hs.getMetadeviceInfo().json()
    for entity in hubspace_device.get_hubspace_devices(
        data, friendly_names, room_names
    ):
        ha_entity = create_ha_entity(hs, debug, entity)
        if ha_entity:
            _LOGGER.debug(f"Adding an entity {ha_entity._childId}")
            entities.append(ha_entity)
    add_entities(entities)

    def my_service(call: ServiceCall) -> None:
        """My first service."""
        _LOGGER.info("Received data" + str(call.data))
        name = SERVICE_NAME
        entity_ids = call.data["entity_id"]
        functionClass = call.data["functionClass"]
        value = call.data["value"]

        if "functionInstance" in call.data:
            functionInstance = call.data["functionInstance"]
        else:
            functionInstance = None

        for entity_id in entity_ids:
            _LOGGER.info("entity_id: " + str(entity_id))
            for i in entities:
                if i.entity_id == entity_id:
                    _LOGGER.info("Found Entity")
                    i.send_command(functionClass, value, functionInstance)

    # Register our service with Home Assistant.
    hass.services.register("hubspace", "send_command", my_service)


def process_color_temps(color_temps: dict) -> list[int]:
    """Determine the supported color temps

    :param color_temps: Result from functions["values"]
    """
    supported_temps = []
    for temp in color_temps:
        color_temp = temp["name"]
        if color_temp.endswith("K"):
            color_temp = int(color_temp[:-1])
        supported_temps.append(color_temp)
    return sorted(supported_temps)


class HubspaceLight(LightEntity):
    """Representation of a HubSpace Light"""

    def __init__(
        self,
        hs,
        friendlyname,
        debug,
        childId=None,
        model=None,
        deviceId=None,
        functions=None,
    ) -> None:
        self._name = friendlyname

        self._debug = debug
        self._state = "off"
        self._childId = childId
        self._model = model
        self._brightness = None
        self._usePowerFunctionInstance = None
        self._hs = hs
        self._deviceId = deviceId
        self._debugInfo = None

        # colorMode == 'color' || 'white'
        self._colorMode = None
        self._colorTemp = None
        self._rgbColor = None
        self._temperature_choices = None
        self._temperature_suffix = None
        self._supported_color_modes = set(ColorMode.ONOFF)
        self._supported_brightness = []

        if functions:
            self.process_functions(functions)

    async def async_setup_entry(hass, entry):
        """Set up the media player platform for Sonos."""

        platform = entity_platform.async_get_current_platform()

        platform.async_register_entity_service(
            "send_command",
            {
                vol.Required("functionClass"): cv.string,
                vol.Required("value"): cv.string,
                vol.Optional("functionInstance"): cv.string,
            },
            "send_command",
        )

    def process_functions(self, functions: list[dict]) -> None:
        """Process the functions and configure the light attributes

        :param functions: Functions that are supported from the API
        """
        for function in functions:
            if function["functionClass"] == "power":
                self._usePowerFunctionInstance = function.get("functionInstance", None)
            elif function["functionClass"] == "color-temperature":
                self._temperature_choices = process_color_temps(function["values"])
                if self._temperature_choices:
                    self._supported_color_modes.add(ColorMode.COLOR_TEMP)
                    self._temperature_suffix = "K"
            elif function["functionClass"] == "brightness":
                temp_bright = hubspace_device.process_range(function["values"][0])
                if temp_bright:
                    self._supported_brightness = temp_bright
                    self._supported_color_modes.add(ColorMode.BRIGHTNESS)

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the display name of this light."""
        return self._childId

    @property
    def color_mode(self) -> ColorMode:
        if self._colorMode == "color":
            return ColorMode.RGB
        return self._colorMode

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        return {*self._supported_color_modes}

    @property
    def brightness(self) -> int or None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        if self._state is None:
            return None
        else:
            return self._state == "on"

    @property
    def min_color_temp_kelvin(self) -> int:
        return min(self._temperature_choices)

    @property
    def max_color_temp_kelvin(self) -> int:
        return max(self._temperature_choices)

    def send_command(self, field_name, field_state, functionInstance=None) -> None:
        self._hs.setState(self._childId, field_name, field_state, functionInstance)

    def set_send_state(self, field_name, field_state) -> None:
        self._hs.setState(self._childId, field_name, field_state)

    def turn_on(self, **kwargs: Any) -> None:
        """Perform power on and set additional attributes"""
        _LOGGER.debug(f"Adjusting light {self._childId} with {kwargs}")
        power_state = {
            "functionClass": "power",
            "value": "on",
        }
        self._state = "on"
        if self._usePowerFunctionInstance:
            power_state["functionInstance"] = self._usePowerFunctionInstance
        states_to_set = [power_state]
        if (
            ATTR_BRIGHTNESS in kwargs
            and ColorMode.BRIGHTNESS in self._supported_color_modes
        ):
            brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
            states_to_set.append(
                {
                    "functionClass": "brightness",
                    "value": _brightness_to_hubspace(brightness),
                }
            )
            self._brightness = brightness
        if (
            ATTR_COLOR_TEMP in kwargs
            and ColorMode.COLOR_TEMP in self._supported_color_modes
        ):
            color_to_set = self._temperature_choices[0]
            # I am not sure how to set specific values, so find the value
            # that is closest without going over
            for color in self._temperature_choices:
                if kwargs[ATTR_COLOR_TEMP_KELVIN] <= color:
                    color_to_set = color
                    break
            states_to_set.append(
                {
                    "functionClass": "color-temperature",
                    "value": f"{color_to_set}K",
                }
            )
            self._colorTemp = color_to_set
        self._hs.set_states(self._childId, states_to_set)

    @property
    def rgb_color(self):
        """Return the rgb value."""
        return self._rgbColor

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "model": self._model,
            "deviceId": self._deviceId,
            "Supported Temperatures": [f"{x}K" for x in self._temperature_choices],
            "Child ID": self._childId,
        }

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._hs.setPowerState(self._childId, "off", self._usePowerFunctionInstance)

    @property
    def should_poll(self):
        """Turn on polling"""
        return True

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        for state in self._hs.get_states(self._childId)["values"]:
            if state["functionClass"] == "power":
                self._state = state["value"]
            elif state["functionClass"] == "color-temperature":
                tmp_state = state["value"]
                if tmp_state.endswith("K"):
                    tmp_state = tmp_state[:-1]
                self._colorTemp = tmp_state
            elif state["functionClass"] == "brightness":
                self._brightness = _brightness_to_hass(state["value"])
            elif state["functionClass"] == "color-mode":
                self._colorMode = state["value"]
            elif state["functionClass"] == "color-rgb":
                self._colorMode = (
                    int(state.get("color-rgb").get("r")),
                    int(state.get("color-rgb").get("g")),
                    int(state.get("color-rgb").get("b")),
                )
