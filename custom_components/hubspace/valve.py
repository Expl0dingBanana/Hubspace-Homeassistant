import logging
from typing import Optional

from homeassistant.components.valve import ValveEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from hubspace_async import HubSpaceState

from . import HubSpaceConfigEntry
from .const import DOMAIN
from .coordinator import HubSpaceDataUpdateCoordinator

logger = logging.getLogger(__name__)


class HubSpaceValve(ValveEntity):
    """HubSpace switch-type that can communicate with Home Assistant

    :ivar _name: Name of the device
    :ivar _hs: HubSpace connector
    :ivar _child_id: ID used when making requests to HubSpace
    :ivar _state: If the device is on / off
    :ivar _bonus_attrs: Attributes relayed to Home Assistant that do not need to be
        tracked in their own class variables
    :ivar _instance: functionInstance within the HS device
    :ivar _current_valve_position: Current position of the valve
    :ivar _reports_position: Reports position of the valve
    """

    def __init__(
        self,
        hs: HubSpaceDataUpdateCoordinator,
        friendly_name: str,
        instance: str,
        child_id: Optional[str] = None,
        model: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> None:
        self._name: str = friendly_name
        self.coordinator = hs
        self._hs = hs.conn
        self._child_id: str = child_id
        self._state: Optional[str] = None
        self._bonus_attrs = {
            "model": model,
            "deviceId": device_id,
            "Child ID": self._child_id,
        }
        # Entity-specific
        self._instance: str = instance
        self._current_valve_position: int | None = None
        self._reports_position: bool = False
        super().__init__(hs, context=self._child_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update_states()
        self.async_write_ha_state()

    def update_states(self) -> None:
        """Load initial states into the device"""
        states: list[HubSpaceState] = self.coordinator.data["states"].get(
            self._child_id, []
        )
        if not states:
            logger.debug(
                "No states found for %s. Maybe hasn't polled yet?", self._child_id
            )
        # functionClass -> internal attribute
        for state in states:
            if state.functionInstance == self._instance:
                self._state = state.value

    @property
    def should_poll(self):
        return False

    @property
    def name(self) -> str:
        """Return the display name"""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the HubSpace ID"""
        return self._child_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._bonus_attrs

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        if self._state is None:
            return None
        else:
            return self._state == "on"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._bonus_attrs["deviceId"])},
            name=self._name,
            model=self._bonus_attrs["model"],
        )

    async def async_open_valve(self, **kwargs) -> None:
        logger.debug("Opening %s on %s", self._instance, self._child_id)
        self._state = "on"
        states_to_set = [
            HubSpaceState(
                functionClass="toggle",
                functionInstance=self._instance,
                value=self._state,
            )
        ]
        await self._hs.set_device_states(self._child_id, states_to_set)
        self.async_write_ha_state()

    async def async_close_valve(self, **kwargs) -> None:
        logger.debug("Closing %s on %s", self._instance, self._child_id)
        self._state = "off"
        states_to_set = [
            HubSpaceState(
                functionClass="toggle",
                functionInstance=self._instance,
                value=self._state,
            )
        ]
        await self._hs.set_device_states(self._child_id, states_to_set)
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HubSpaceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Fan entities from a config_entry."""
    coordinator_hubspace: HubSpaceDataUpdateCoordinator = (
        entry.runtime_data.coordinator_hubspace
    )
    entities: list[HubSpaceValve] = []
    for entity in coordinator_hubspace.data["devices"]:
        if entity.device_class == "water-timer":
            for function in entity.functions:
                if function["functionClass"] != "toggle":
                    continue
                instance = function["functionInstance"]
                ha_entity = HubSpaceValve(
                    coordinator_hubspace,
                    entity.friendly_name,
                    instance,
                    child_id=entity.id,
                    model=entity.model,
                    device_id=entity.device_id,
                )
                logger.debug(
                    f"Adding a %s [%s] @ %s", entity.device_class, entity.id, instance
                )
                entities.append(ha_entity)
        else:
            logger.debug(
                f"Unable to process the entity {entity.friendly_name} of class {entity.device_class}"
            )
            continue
    async_add_entities(entities)
