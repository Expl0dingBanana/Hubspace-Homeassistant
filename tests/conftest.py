import logging

import pytest

from custom_components.hubspace import hubspace


@pytest.fixture
def mocked_hubspace(mocker):
    """Mock all HubSpace functionality but ensure the class is correct"""
    hs_mock = mocker.patch.object(hubspace, "HubSpace", autospec=True)
    return hs_mock


@pytest.fixture(autouse=True)
def set_debug_mode(caplog):
    # Force capture of all debug logging. This is useful if you want to verify
    # log messages with `<message> in caplog.text`. If you run
    # pytest -rP it will display all log messages, including passing tests.
    caplog.set_level(logging.DEBUG)
