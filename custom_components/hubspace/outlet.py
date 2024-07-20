from typing import Any

import voluptuous as vol
from homeassistant.components.light import ColorMode
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform


class HubspaceOutlet:
    """Representation of an Awesome Light."""

    def __init__(
        self,
        hs,
        friendlyname,
        outletIndex,
        debug,
        childId=None,
        model=None,
        deviceId=None,
        deviceClass=None,
    ) -> None:
        """Initialize an AwesomeLight."""

        self._name = friendlyname + "_outlet_" + outletIndex

        self._debug = debug
        self._state = "off"
        self._childId = childId
        self._model = model
        self._brightness = None
        self._usePrimaryFunctionInstance = False
        self._hs = hs
        self._deviceId = deviceId
        self._debugInfo = None
        self._outletIndex = outletIndex

        if None in (childId, model, deviceId, deviceClass):
            [
                self._childId,
                self._model,
                self._deviceId,
                deviceClass,
            ] = self._hs.getChildId(friendlyname)

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

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the display name of this light."""
        return self._childId + "_" + self._outletIndex

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        return ColorMode.ONOFF

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        return {self.color_mode}

    def send_command(self, field_name, field_state, functionInstance=None) -> None:
        self._hs.setState(self._childId, field_name, field_state, functionInstance)

    def set_send_state(self, field_name, field_state) -> None:
        self._hs.setState(self._childId, field_name, field_state)

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        if self._state is None:
            return None
        else:
            return self._state == "on"

    def turn_on(self, **kwargs: Any) -> None:
        self._hs.setStateInstance(
            self._childId, "toggle", "outlet-" + self._outletIndex, "on"
        )
        # self.update()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attr = {}
        attr["model"] = self._model
        attr["deviceId"] = self._deviceId + "_" + self._outletIndex
        attr["devbranch"] = False

        attr["debugInfo"] = self._debugInfo

        return attr

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._hs.setStateInstance(
            self._childId, "toggle", "outlet-" + self._outletIndex, "off"
        )
        # self.update()

    @property
    def should_poll(self):
        """Turn on polling"""
        return True

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self._hs.getStateInstance(
            self._childId, "toggle", "outlet-" + self._outletIndex
        )
        if self._debug:
            self._debugInfo = self._hs.getDebugInfo(self._childId)
