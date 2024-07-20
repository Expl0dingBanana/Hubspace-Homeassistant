"""Platform for fan integration."""

import logging
from contextlib import suppress
from typing import Any, Optional, Union

import requests
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from . import hubspace_device

logger = logging.getLogger(__name__)

# Import the device class from the component that you want to support
from homeassistant.components.fan import FanEntity, FanEntityFeature

from . import CONF_DEBUG, CONF_FRIENDLYNAMES, CONF_ROOMNAMES
from .hubspace import HubSpace
from .hubspace_device import process_range

PRESET_HS_TO_HA = {"comfort-breeze": "breeze"}

PRESET_HA_TO_HS = {val: key for key, val in PRESET_HS_TO_HA.items()}


class HubspaceFan(FanEntity):
    """HubSpace fan that can communicate with Home Assistant

    :ivar _name: Name of the device
    :ivar _hs: HubSpace connector
    :ivar _child_id: ID used when making requests to HubSpace
    :ivar _state: If the device is on / off
    :ivar _current_direction: Current direction of the device, or if a
        direction change is in progress
    :ivar _preset_mode: Current preset mode of the device, such as breeze
    :ivar _preset_modes: List of available preset modes for the device
    :ivar _supported_features: Features that the fan supports, where each
        feature is an Enum from FanEntityFeature.
    :ivar _fan_speeds: List of available fan speeds for the device from HubSpace
    :ivar _bonus_attrs: Attributes relayed to Home Assistant that do not need to be
        tracked in their own class variables
    :ivar _instance_attrs: Additional attributes that are required when
        POSTing to HubSpace

    :param hs: HubSpace connector
    :param friendly_name: The friendly name of the device
    :param child_id: ID used when making requests to HubSpace
    :param model: Model of the device
    :param device_id: Parent Device ID
    :param functions: List of supported functions for the device
    """

    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        hs: HubSpace,
        friendly_name: str,
        child_id: Optional[str] = None,
        model: Optional[str] = None,
        device_id: Optional[str] = None,
        functions: Optional[list[dict]] = None,
    ) -> None:
        self._name: str = friendly_name
        self._hs = hs
        self._child_id: str = child_id
        self._state: Optional[str] = None
        self._current_direction: Optional[str] = None
        self._preset_mode: Optional[str] = None
        self._preset_modes: set[str] = set()
        self._supported_features: FanEntityFeature = FanEntityFeature(0)
        self._fan_speeds: list[Union[str, int]] = []
        self._fan_speed: Optional[str] = None
        self._bonus_attrs = {
            "model": model,
            "deviceId": device_id,
            "Child ID": self._child_id,
        }
        self._instance_attrs: dict[str, str] = {}
        self.update_states()
        if functions:
            self.process_functions(functions)

    def process_functions(self, functions: list[dict]) -> None:
        """Process available functions

        :param functions: Functions that are supported from the API
        """
        for function in functions:
            if function["functionInstance"]:
                self._instance_attrs[function["functionClass"]] = function[
                    "functionInstance"
                ]
            if function["functionClass"] == "toggle":
                self._supported_features |= FanEntityFeature.PRESET_MODE
                self._preset_modes.add(function["functionInstance"])
                self._instance_attrs.pop(function["functionClass"])
                logger.debug("Adding a new feature - preset, %s", function["functionInstance"])
            elif function["functionClass"] == "fan-speed":
                self._supported_features |= FanEntityFeature.SET_SPEED
                tmp_speed = set()
                for value in function["values"]:
                    # I am not sure fan speeds will be a range, but providing that
                    # functionality
                    if value["range"]:
                        tmp_speed = set(process_range(value["range"]))
                    elif not value["name"].endswith("-000"):
                        tmp_speed.add(value["name"])
                self._fan_speeds = list(sorted(tmp_speed))
                logger.debug("Adding a new feature - fan speed, %s", self._fan_speeds)
            elif function["functionClass"] == "fan-reverse":
                self._supported_features |= FanEntityFeature.DIRECTION
                logger.debug("Adding a new feature - direction")
            elif function["functionClass"] == "power":
                logger.debug("Adding a new feature - on / off")
                # This code is in the mainline but unreleased
                with suppress(AttributeError):
                    self._supported_features |= FanEntityFeature.TURN_ON
                    self._supported_features |= FanEntityFeature.TURN_OFF
            else:
                logger.debug("Unsupported feature found, %s", function["functionClass"])
                self._instance_attrs.pop(function["functionClass"], None)

    def update_states(self) -> None:
        """Load initial states into the device"""
        states = self._hs.get_states(self._child_id)
        additional_attrs = [
            "wifi-ssid",
            "wifi-mac-address",
            "available",
            "ble-mac-address",
        ]
        # functionClass -> internal attribute
        for state in states["values"]:
            if state["functionClass"] == "toggle":
                if state["value"] == "enabled":
                    self._preset_mode = state["functionInstance"]
            elif state["functionClass"] == "fan-speed":
                self._fan_speed = state["value"]
            elif state["functionClass"] == "fan-reverse":
                self._current_direction = state["value"]
            elif state["functionClass"] == "power":
                self._state = state["value"]
            elif state["functionClass"] in additional_attrs:
                self._bonus_attrs[state["functionClass"]] = state["value"]

    def update(self):
        self.update_states()

    @property
    def name(self) -> str:
        """Return the display name of this fan."""
        return self._name

    @property
    def unique_id(self) -> str:
        return self._child_id + "_fan"

    @property
    def is_on(self) -> bool:
        return self._state == "on"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._bonus_attrs

    @property
    def current_direction(self):
        return self._current_direction

    @property
    def oscillating(self):
        """Determine if the fan is currently oscillating

        I do not believe any HubSpace fan supports oscillation but
        adding in the property.
        """
        return False

    @property
    def percentage(self):
        if self._fan_speed:
            if self._fan_speed.endswith("-000"):
                return 0
            return ordered_list_item_to_percentage(self._fan_speeds, self._fan_speed)
        return 0

    @property
    def preset_mode(self):
        return PRESET_HS_TO_HA.get(self._preset_mode, None)

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def speed_count(self):
        return len(self._fan_speeds)

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def should_poll(self):
        return True

    def turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        state_updates = []
        with suppress(AttributeError):
            if not self._supported_features & FanEntityFeature.TURN_ON:
                raise NotImplementedError
        self._state = "on"
        state_updates.append(
            {
                "functionClass": "power",
                "functionInstance": self._instance_attrs.get("power", None),
                "value": "on",
            }
        )
        self._hs.set_states(self._child_id, state_updates)
        self.set_percentage(percentage)
        self.set_preset_mode(preset_mode)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        with suppress(AttributeError):
            if not self._supported_features & FanEntityFeature.TURN_OFF:
                raise NotImplementedError
        self._state = "off"
        state_updates =[
            {
                "functionClass": "power",
                "functionInstance": self._instance_attrs.get("power", None),
                "value": "off",
            }
        ]
        self._hs.set_states(self._child_id, state_updates)

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if self._supported_features & FanEntityFeature.SET_SPEED:
            self._fan_speed = percentage_to_ordered_list_item(
                self._fan_speeds, percentage
            )
            self._hs.setState(self._child_id, "fan-speed", self._fan_speed, instanceField=self._instance_attrs.get("fan-speed", None))

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if self._supported_features & FanEntityFeature.PRESET_MODE:
            if not preset_mode:
                self._hs.setState(self._child_id, "toggle", "disabled", instanceField=self._preset_mode)
                self._preset_mode = None
            else:
                self._preset_mode = PRESET_HS_TO_HA.get(preset_mode, None)
                self._hs.setState(self._child_id, "toggle","enabled", instanceField=self._preset_mode)

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if self._supported_features & FanEntityFeature.DIRECTION:
            self._current_direction = direction
            self._hs.setState(self._child_id, "fan-reverse", direction, instanceField=self._instance_attrs.get("fan-reverse", None))


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Add all fans"""
    username = config[CONF_USERNAME]
    password = config.get(CONF_PASSWORD)
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
        if entity.device_class != "fan":
            logger.debug(f"Unable to process the entity {entity.friendly_name} of class {entity.device_class}")
            continue
        ha_entity = HubspaceFan(
            hs,
            entity.friendly_name,
            child_id=entity.id,
            model=entity.model,
            device_id=entity.device_id,
            functions=entity.functions,
        )
        logger.debug(f"Adding an entity {ha_entity._child_id}")
        entities.append(ha_entity)
    add_entities(entities)
