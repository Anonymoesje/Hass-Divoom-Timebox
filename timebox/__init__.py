"""Timebox integration"""
from __future__ import annotations
import asyncio
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform, CONF_URL, CONF_PORT, CONF_MAC, CONF_NAME, CONF_PATH
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, SERVICE_ACTION, TIMEOUT
from .timebox import Timebox
from .notify import TimeboxService, async_unload_entry as notify_async_unload_entry

_LOGGER = logging.getLogger(__name__)

# Supported Platforms
PLATFORMS = [
    # "binary_sensor",
    # "button",
    # "light",
    # "media_player",
    # "number",
    # "sensor",
    # "switch",
    "light"
]

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistantType, config: dict):
    """Set up the timebox component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up timebox from the config entry."""
    
    entry_data = entry.data
    timebox_url = entry_data[CONF_URL]
    timebox_port = entry_data[CONF_PORT]
    timebox_mac = entry_data[CONF_MAC]
    timebox_name = entry_data[CONF_NAME]
    image_dir = entry_data[CONF_PATH]
    
    # Setup timebox singleton
    timebox = Timebox(
        hass,
        async_get_clientsession(hass, False), #TODO test with ssl
        timebox_url, 
        timebox_port, 
        timebox_mac, 
        image_dir, 
        timebox_name
    )
    
    if not timebox.isConnected():
        _LOGGER.error("No connection to Timebox, check your bluetooth connection!")
        return False # Return false because integration cannot operate without connection
    else:
        _LOGGER.info("Timebox succesfully connected")

# Store an instance of the "connecting" class that does the work of speaking with the actual devices.
    hass.data[DOMAIN][entry.entry_id] = timebox
    #hass.data.setdefault(DOMAIN, {})[entry.entry_id] = timebox

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    await register_services(hass)
    return True


async def register_services(hass) -> None:
    """Register services after startup."""
    _LOGGER.debug("Completing registering services.")
    hass.services.async_register(DOMAIN, SERVICE_ACTION, _send_service)
    return True

async def _send_service(service):
    body = service.data.get("body")
    await TimeboxService.send_message(body), None

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok