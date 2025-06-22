"""Initializations for Clash."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import ClashAPI
from .device import DeviceInfoManager
from .dispatcher import ClashDispatcher
from .worker import ClashWorker

# from .services import ClashServicesSetup

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    # Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
]


@dataclass
class RuntimeData:
    """Class to hold integration data."""

    dispatcher: ClashDispatcher
    api: ClashAPI
    worker: ClashWorker


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[RuntimeData]
) -> bool:
    """Set up Clash from a config entry."""
    _LOGGER.debug("Setting up Clash entry: %s", entry.entry_id)

    # Set up the dispatcher and API
    dispatcher = ClashDispatcher(hass)
    api = ClashAPI(entry)
    worker = ClashWorker(entry, api, dispatcher)
    entry.runtime_data = RuntimeData(dispatcher, api, worker)

    if await api.check_connection():
        _LOGGER.debug("Clash API connection established")
    else:
        _LOGGER.error("Failed to connect to Clash API")
        raise ConfigEntryNotReady

    # Initialize device info manager and register it
    manager = DeviceInfoManager(dispatcher, entry)
    manager.register_manager(hass)

    # Initialize all platforms
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    # Register reload handler for the config entry
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Start fetching data from the API
    api.start_fetching()
    # ClashServicesSetup(hass, config_entry)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config options update."""
    await hass.config_entries.async_reload(entry.entry_id)


# async def async_remove_config_entry_device(
#     hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
# ) -> bool:
#     """Handle entry removal."""

#     return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry[RuntimeData]
) -> bool:
    """Unload a config entry."""

    # for service in hass.services.async_services_for_domain(DOMAIN):
    #     hass.services.async_remove(DOMAIN, service)
    # entry.runtime_data.cancel_update_listener()
    api = entry.runtime_data.api
    worker = entry.runtime_data.worker
    if worker:
        await worker.stop_fetching()
    if api:
        await api.close()
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    # return unload_ok and await _async_unload_entry(hass, entry)
    # if unload_ok:
    #     hass.data[DOMAIN].pop(config_entry.entry_id)
    # return unload_ok
