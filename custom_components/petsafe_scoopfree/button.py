"""Support for petsafe scooper reset button."""
from __future__ import annotations
import logging
import json
import asyncio

from homeassistant.components.button import (
    ButtonEntity,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .hub import PetSafeHub
from petsafe_scoopfree import devices

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up petsafe config entry."""
    coordinator_device_sensor = hass.data[DOMAIN][entry.entry_id][
        "coordinator_device_sensor"
    ]
    hub = hass.data[DOMAIN][entry.entry_id] = PetSafeHub(hass, entry.data)
    async_add_entities(
        [
            PetSafeResetButton(coordinator_device_sensor, id, hub=hub, device=devices)
            for _, id in enumerate(coordinator_device_sensor.data)
        ]
    )

    async_add_entities(
        [
            PetSafeRakeButton(coordinator_device_sensor, id, hub=hub, device=devices)
            for _, id in enumerate(coordinator_device_sensor.data)
        ]
    )


class PetSafeResetButton(CoordinatorEntity, ButtonEntity):
    """Petsafe reset button."""

    def __init__(
        self, coordinator, identifier, hub: PetSafeHub, device: devices
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.hub = hub
        self.device = device
        self._id = identifier
        self._attr_icon = "mdi:lock-reset"
        self._attr_entity_category = EntityCategory.CONFIG
        device_name = self.coordinator.data[identifier]["friendlyName"]
        thing_name = self.coordinator.data[identifier]["thingName"]
        self._attr_name = f"{device_name} Reset"
        self._attr_unique_id = f"{thing_name} reset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data[identifier]["thingName"])}
        )

    async def async_press(self) -> None:
        """Triggers the reset counter button press service."""
        _LOGGER.info("Triggered %s", self._attr_unique_id)
        loop = asyncio.get_event_loop()
        client = await self.hub.login()
        scoopers = await loop.run_in_executor(None, self.device.get_scoopers, client)
        for scooper in scoopers:
            device = json.loads(scooper.to_json())
            if device["thingName"] == self._attr_unique_id.split(" ")[0]:
                _LOGGER.info("reseting %s", self._attr_unique_id)
                await loop.run_in_executor(None, scooper.reset)
                self.coordinator.async_set_updated_data(True)


class PetSafeRakeButton(CoordinatorEntity, ButtonEntity):
    """Petsafe rake button."""

    def __init__(
        self, coordinator, identifier, hub: PetSafeHub, device: devices
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.hub = hub
        self.device = device
        self._id = identifier
        self._attr_icon = "mdi:rake"
        self._attr_entity_category = EntityCategory.CONFIG
        device_name = self.coordinator.data[identifier]["friendlyName"]
        thing_name = self.coordinator.data[identifier]["thingName"]
        self._attr_name = f"{device_name} Rake"
        self._attr_unique_id = f"{thing_name} rake"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data[identifier]["thingName"])}
        )

    async def async_press(self) -> None:
        """Triggers the reset counter button press service."""
        _LOGGER.info("Triggered %s", self._attr_unique_id)
        loop = asyncio.get_event_loop()
        client = await self.hub.login()
        scoopers = await loop.run_in_executor(None, self.device.get_scoopers, client)
        for scooper in scoopers:
            device = json.loads(scooper.to_json())
            if device["thingName"] == self._attr_unique_id.split(" ")[0]:
                _LOGGER.info("raking %s", self._attr_unique_id)
                await loop.run_in_executor(None, scooper.rake_now)
                self.coordinator.async_set_updated_data(True)
