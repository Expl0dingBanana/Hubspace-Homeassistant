"""Test the integration between Home Assistant Locks and Afero devices."""

from aioafero import AferoState
from aioafero.v1.controllers.lock import features
from homeassistant.helpers import entity_registry as er
import pytest

from .utils import create_devices_from_data, hs_raw_from_dump, modify_state

lock_tbd = create_devices_from_data("door-lock-TBD.json")
lock_tbd_instance = lock_tbd[0]
lock_id = "lock.friendly_device_0_lock"


@pytest.fixture
async def mocked_entity(mocked_entry):
    """Initialize a mocked Lock and register it within Home Assistant."""
    hass, entry, bridge = mocked_entry
    await bridge.generate_devices_from_data(lock_tbd)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield hass, entry, bridge
    await bridge.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "dev",
        "expected_entities",
    ),
    [
        (
            lock_tbd_instance,
            [lock_id],
        ),
    ],
)
async def test_async_setup_entry(dev, expected_entities, mocked_entry):
    """Ensure locks are properly discovered and registered with Home Assistant."""
    try:
        hass, entry, bridge = mocked_entry
        await bridge.generate_devices_from_data([dev])
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_reg = er.async_get(hass)
        for entity in expected_entities:
            assert entity_reg.async_get(entity) is not None
    finally:
        await bridge.close()


@pytest.mark.asyncio
async def test_unlock(mocked_entity):
    """Ensure the service call unlock works as expected."""
    hass, _, bridge = mocked_entity
    await hass.services.async_call(
        "lock",
        "unlock",
        {"entity_id": lock_id},
        blocking=True,
    )
    update_call = bridge.request.call_args_list[-1]
    assert update_call.args[0] == "put"
    payload = update_call.kwargs["json"]
    assert payload["metadeviceId"] == lock_tbd_instance.id
    update = payload["values"][0]
    assert update["functionClass"] == "lock-control"
    assert update["functionInstance"] is None
    assert update["value"] == "unlocking"
    # Now generate update event by emitting the json we've sent as incoming event
    lock_update = create_devices_from_data("door-lock-TBD.json")[0]
    modify_state(
        lock_update,
        AferoState(
            functionClass="lock-control",
            functionInstance=None,
            value="unlocking",
        ),
    )
    await bridge.generate_devices_from_data([lock_update])
    await hass.async_block_till_done()
    assert (
        bridge.locks[lock_update.id].position.position
        == features.CurrentPositionEnum.UNLOCKING
    )
    assert hass.states.get(lock_id).state == "opening"


@pytest.mark.asyncio
async def test_lock(mocked_entity):
    """Ensure the service call lock works as expected."""
    hass, _, bridge = mocked_entity
    await hass.services.async_call(
        "lock",
        "lock",
        {"entity_id": lock_id},
        blocking=True,
    )
    update_call = bridge.request.call_args_list[-1]
    assert update_call.args[0] == "put"
    payload = update_call.kwargs["json"]
    assert payload["metadeviceId"] == lock_tbd_instance.id
    update = payload["values"][0]
    assert update["functionClass"] == "lock-control"
    assert update["functionInstance"] is None
    assert update["value"] == "locking"
    # Now generate update event by emitting the json we've sent as incoming event
    lock_update = create_devices_from_data("door-lock-TBD.json")[0]
    modify_state(
        lock_update,
        AferoState(
            functionClass="lock-control",
            functionInstance=None,
            value="locking",
        ),
    )
    await bridge.generate_devices_from_data([lock_update])
    await hass.async_block_till_done()
    assert (
        bridge.locks[lock_update.id].position.position
        == features.CurrentPositionEnum.LOCKING
    )
    assert hass.states.get(lock_id).state == "locking"
    # Now generate update event by emitting the json we've sent as incoming event
    lock_update = create_devices_from_data("door-lock-TBD.json")[0]
    modify_state(
        lock_update,
        AferoState(
            functionClass="lock-control",
            functionInstance=None,
            value="locked",
        ),
    )
    await bridge.generate_devices_from_data([lock_update])
    await hass.async_block_till_done()
    assert (
        bridge.locks[lock_update.id].position.position
        == features.CurrentPositionEnum.LOCKED
    )
    assert hass.states.get(lock_id).state == "locked"


@pytest.mark.asyncio
async def test_add_new_device(mocked_entry):
    """Ensure newly added devices are properly discovered and registered with Home Assistant."""
    hass, entry, bridge = mocked_entry
    assert len(bridge.devices.items) == 0
    # Register callbacks
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert len(bridge.devices.subscribers) > 0
    assert len(bridge.devices.subscribers["*"]) > 0
    # Now generate update event by emitting the json we've sent as incoming event
    afero_data = hs_raw_from_dump("door-lock-TBD.json")
    await bridge.generate_events_from_data(afero_data)
    await bridge.async_block_until_done()
    await hass.async_block_till_done()
    assert len(bridge.devices.items) == 1
    entity_reg = er.async_get(hass)
    await hass.async_block_till_done()
    for entity in [lock_id]:
        assert entity_reg.async_get(entity) is not None
