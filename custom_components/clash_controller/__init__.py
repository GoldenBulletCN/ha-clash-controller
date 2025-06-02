"""Initializations for Clash Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import ClashCoordinator
# from .services import ClashServicesSetup

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    # Platform.BUTTON,
    Platform.SELECT,
    # Platform.SENSOR,
]


@dataclass
class RuntimeData:
    """Class to hold integration data."""

    coordinator: DataUpdateCoordinator
    cancel_update_listener: Callable


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[RuntimeData]
) -> bool:
    """Set up Clash Controller from a config entry."""
    _LOGGER.debug("Setting up Clash Controller entry: %s", entry.entry_id)
    # Generate a coordinator for the entry and fetch initial data
    coordinator = ClashCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.error("Error during coordinator setup: %s", e)
        raise ConfigEntryNotReady from e
    # if not await coordinator.api.connected():
    #     _LOGGER.error("API not connected when setting up the entry")
    #     raise ConfigEntryNotReady

    async def _update_device_info():
        """Update device information if coordinator data changes."""
        device_registry = dr.async_get(hass)
        manufacturer = coordinator.data.get("manufacturer", "Unknown")
        model = coordinator.data.get("model", "Unknown")
        sw_version = coordinator.data.get("version", "Unknown")
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name="TODO",
            manufacturer=manufacturer,
            model=model,
            sw_version=sw_version,
        )
        if (
            device.manufacturer != manufacturer
            or device.model != model
            or device.sw_version != sw_version
        ):
            device_registry.async_update_device(
                device.id, manufacturer=manufacturer, model=model, sw_version=sw_version
            )
            _LOGGER.info(
                "Updated device info for %s: %s %s %s",
                device.id,
                manufacturer,
                model,
                sw_version,
            )

    # Create device info
    await _update_device_info()

    # Register a listener to update device info when coordinator data changes
    coordinator.async_add_listener(_update_device_info)

    cancel_update_listener = entry.add_update_listener(_async_update_listener)
    entry.runtime_data = RuntimeData(coordinator, cancel_update_listener)
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    # ClashServicesSetup(hass, config_entry)
    return True


async def _async_update_listener(hass: HomeAssistant, config_entry):
    """Handle config options update."""

    await hass.config_entries.async_reload(config_entry.entry_id)


# async def async_remove_config_entry_device(
#     hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
# ) -> bool:
#     """Handle entry removal."""

#     return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # for service in hass.services.async_services_for_domain(DOMAIN):
    #     hass.services.async_remove(DOMAIN, service)
    entry.runtime_data.cancel_update_listener()
    coordinator = entry.runtime_data.coordinator
    if coordinator:
        await coordinator.api.close_session()
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    # return unload_ok and await _async_unload_entry(hass, entry)
    # if unload_ok:
    #     hass.data[DOMAIN].pop(config_entry.entry_id)
    # return unload_ok
