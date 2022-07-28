"""The Petsafe Scoopfree integration."""
import asyncio
from datetime import timedelta
import logging

from petsafe_scoopfree import devices, PetSafeClient
import json

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import Platform, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# from .hub import PetSafeHub

from .const import (
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_ACCESS_TOKEN,
    PET_DATA,
    DOMAIN,
    ENABLE_PET,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

device_gids = []
device_information = {}


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the petsafe scooper component."""
    hass.data.setdefault(DOMAIN, {})
    conf = config.get(DOMAIN)
    if not conf:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={
                CONF_EMAIL: conf[CONF_EMAIL],
                CONF_ID_TOKEN: conf[CONF_ID_TOKEN],
                CONF_REFRESH_TOKEN: conf[CONF_REFRESH_TOKEN],
                CONF_ACCESS_TOKEN: conf[CONF_ACCESS_TOKEN],
            },
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up petsafe scooper from a config entry."""
    # hub = hass.data[DOMAIN][entry.entry_id] = PetSafeHub(hass, entry.data)
    global device_gids
    global device_information
    device_gids = []
    device_information = {}
    loop = asyncio.get_event_loop()
    coordinator_device_sensor = None
    entry_data = entry.data

    try:
        client = await loop.run_in_executor(
            None,
            PetSafeClient,
            entry_data[CONF_EMAIL],
            entry_data[CONF_ID_TOKEN],
            entry_data[CONF_REFRESH_TOKEN],
            entry_data[CONF_ACCESS_TOKEN],
        )
    except Exception as ex:
        _LOGGER.error("Unable to connect to petsafe API")
        raise ex

    try:
        # get scooper devices
        scoopers = await loop.run_in_executor(None, devices.get_scoopers, client)
        _LOGGER.info("Found {0} petsafe devices".format(len(scoopers)))
        for device in scoopers:
            device = json.loads(device.to_json())
            if not device["thingName"] in device_gids:
                device_gids.append(device["thingName"])
                device_information[device["thingName"]] = device

        async def async_update_data():
            """Fetch data from API endpoint at a 1 min interval
            This is the place to pre-process the data to lookup tables
            so entities can quickly look up their data.
            """
            return await update_sensors(client)

        coordinator_device_sensor = DataUpdateCoordinator(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="sensor",
            update_method=async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(minutes=1),
        )
        await coordinator_device_sensor.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning(
            "Exception while setting up Petsafe Scoopfree. Will retry. %s", err
        )
        raise ConfigEntryNotReady(
            f"Exception while setting up Petsafe Scoopfree. Will retry. {err}"
        )

    hass.data[DOMAIN][entry.entry_id] = {
        PET_DATA: devices,
        "coordinator_device_sensor": coordinator_device_sensor,
    }

    try:
        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )
    except Exception as err:
        _LOGGER.warning("Error setting up platforms: %s", err)
        raise ConfigEntryNotReady(f"Error setting up platforms: {err}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_sensors(client):
    try:
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        data = {}
        device_ids = []
        loop = asyncio.get_event_loop()

        device_dict = await loop.run_in_executor(None, devices.get_scoopers, client)
        for device in device_dict:
            device = json.loads(device.to_json())
            if not device["thingName"] in device_ids:
                device_ids.append(device["thingName"])
                data[device["thingName"]] = device
        return data
    except Exception as err:
        _LOGGER.error("Error communicating with Petsafe Scoopfree API: %s", err)
        raise UpdateFailed(f"Error communicating with Petsafe Scoopfree API: {err}")
