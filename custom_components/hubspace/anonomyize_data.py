from uuid import uuid4
from hubspace_async import HubSpaceConnection, HubSpaceState, HubSpaceDevice
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)


FNAME_IND = 0


async def generate_anon_data(conn: HubSpaceConnection):
    devices = await conn.devices
    fake_devices = []
    parents = {}
    for dev in devices.values():
        fake_devices.append(anonymize_device(dev, parents))
    return fake_devices


def anonymize_device(dev: HubSpaceDevice, parent_mapping: dict):
    fake_dev = asdict(dev)
    global FNAME_IND
    # Modify the name
    fake_dev["friendly_name"] = f"friendly-device-{FNAME_IND}"
    FNAME_IND += 1
    # Modify the id
    fake_dev["id"] = str(uuid4())
    # Remove parent id
    parent = dev.device_id
    if parent not in parent_mapping:
        parent_mapping[parent] = str(uuid4())
    fake_dev["device_id"] = parent_mapping[parent]
    fake_dev["states"] = []
    for ind, state in enumerate(dev.states):
        fake_dev["states"].append(anonymize_state(state))
    return fake_dev


def anonymize_state(state:HubSpaceState):
    fake_state = asdict(state)
    fake_state["lastUpdateTime"] = 0
    if fake_state["functionClass"] == "wifi-ssid":
        fake_state["value"] = str(uuid4())
    elif isinstance(state.value, str):
        if "mac" in state.functionClass:
            fake_state["value"] = str(uuid4())
    return fake_state
