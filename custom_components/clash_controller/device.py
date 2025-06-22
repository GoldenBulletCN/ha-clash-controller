"""Device information manager for Clash."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .base import BaseManager
from .const import DOMAIN, SIGNAL_DEVICE_INFO_UPDATE
from .dispatcher import ClashDispatcher

_LOGGER = logging.getLogger(__name__)


class DeviceInfoManager(BaseManager):
    """Manages device information for Clash."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the device info manager."""
        super().__init__(dispatcher, entry, SIGNAL_DEVICE_INFO_UPDATE)

    async def _handle_dispatcher_update(self) -> None:
        """Update device information if it changes."""
        device_registry = dr.async_get(self.hass)
        manufacturer = self.dispatcher.data.manufacturer
        model = self.dispatcher.data.model
        sw_version = self.dispatcher.data.version
        device = device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="Clash",
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
