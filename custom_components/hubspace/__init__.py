"""Hubspace Lights integration."""

import logging
from typing import Final

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

CONF_FRIENDLYNAMES: Final = "friendlynames"
CONF_ROOMNAMES: Final = "roomnames"
CONF_DEBUG: Final = "debug"
