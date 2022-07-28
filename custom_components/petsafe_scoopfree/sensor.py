"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN

STATE_ATTR_TZ = "timezone"
STATE_ATTR_CREATED_AT = "Created At"
STATE_ATTR_PETS_USING = "Number of Pets Using"
STATE_ATTR_UPDATED_AT = "Updated At"
STATE_ATTR_PRODUCT_NAME = "Product Name"
STATE_ATTR_RAKE_COUNT = "Rake Count"
STATE_ATTR_RAKE_DELAY = "Rake Delay Time Min"
STATE_ATTR_DEVICE_STATUS = "Device Status"
STATE_ATTR_CONN_STATIS = "Connection Status"

_LOGGER = logging.getLogger(__name__)

# def setup_platform(hass, config, add_entities, discovery_info=None):
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator_device_sensor = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator_device_sensor"
    ]

    if coordinator_device_sensor:
        async_add_entities(
            PetSafeDeviceSensor(coordinator_device_sensor, id)
            for _, id in enumerate(coordinator_device_sensor.data)
        )


class PetSafeDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of petsafe scoopfree devices."""

    def __init__(self, coordinator, identifier):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._id = identifier
        device_name = self.coordinator.data[identifier]["friendlyName"]
        self._name = f"petsafe_scoopfree_{device_name}"
        self._attr_name = f"{device_name}"
        self._state = self.coordinator.data[identifier]["shadow"]["state"]["reported"][
            "connectionStatus"
        ]
        self._attr_friendly_name = self._name
        self._attr_icon = "mdi:inbox-arrow-up-outline"
        self._fw_version = self.coordinator.data[self._id]["shadow"]["state"][
            "reported"
        ]["firmware"]
        self._status = self.coordinator.data[self._id]["shadow"]["state"]["reported"][
            "deviceStatus"
        ]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._id in self.coordinator.data:
            status = self._status
            return status
        return None

    @property
    def unique_id(self):
        """Unique ID for the sensor"""
        return f"sensor.petsafe_scoopfree.{self._id}"

    @property
    def device_info(self):
        device_name = self.name
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (
                    DOMAIN,
                    "{0}".format(self._id),
                )
            },
            "name": device_name,
            "model": "Scoopfree2",
            "sw_version": self._fw_version,
            "manufacturer": "Petsafe",
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes of petsafe scoopfree."""
        return {
            STATE_ATTR_TZ: self.coordinator.data[self._id]["tz"],
            STATE_ATTR_CREATED_AT: self.coordinator.data[self._id]["createdAt"],
            STATE_ATTR_PETS_USING: self.coordinator.data[self._id]["numberOfPetsUsing"],
            STATE_ATTR_UPDATED_AT: self.coordinator.data[self._id]["updatedAt"],
            STATE_ATTR_PRODUCT_NAME: self.coordinator.data[self._id]["productName"],
            STATE_ATTR_RAKE_COUNT: self.coordinator.data[self._id]["shadow"]["state"][
                "reported"
            ]["rakeCount"],
            STATE_ATTR_RAKE_DELAY: self.coordinator.data[self._id]["shadow"]["state"][
                "reported"
            ]["rakeDelayTime"],
            STATE_ATTR_DEVICE_STATUS: self.coordinator.data[self._id]["shadow"][
                "state"
            ]["reported"]["deviceStatus"],
            STATE_ATTR_CONN_STATIS: self.coordinator.data[self._id]["shadow"]["state"][
                "reported"
            ]["connectionStatus"],
        }
