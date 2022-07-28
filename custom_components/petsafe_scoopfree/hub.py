"""A wrapper 'hub' for petsafe."""
from __future__ import annotations

from collections.abc import Mapping
import logging

from petsafe_scoopfree import PetSafeClient, devices as Devices

from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_ACCESS_TOKEN,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 60


class PetSafeHub:
    """A Petsafe hub wrapper class."""

    # account: Account
    devices: Devices
    client: PetSafeClient

    def __init__(self, hass: HomeAssistant, entry: Mapping) -> None:
        """Initialize the Petsafe hub."""
        self._data = entry
        self._hass = hass

    async def login(self):
        """Login to petsafe."""
        entry_data = self._data
        try:
            results = await self._hass.async_add_executor_job(
                PetSafeClient,
                entry_data[CONF_EMAIL],
                entry_data[CONF_ID_TOKEN],
                entry_data[CONF_REFRESH_TOKEN],
                entry_data[CONF_ACCESS_TOKEN],
            )
            return results
        except Exception as ex:
            _LOGGER.error("Unable to connect to petsafe API")
            raise ex
