"""Sensor platform for Clash Controller."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import BaseEntity
from .const import (
    SIGNAL_ACTIVE_CONNECTIONS_UPDATE,
    SIGNAL_DOWNLOAD_SPEED_UPDATE,
    SIGNAL_DOWNLOAD_TOTAL_UPDATE,
    SIGNAL_MEMORY_USAGE_UPDATE,
    SIGNAL_UPLOAD_SPEED_UPDATE,
    SIGNAL_UPLOAD_TOTAL_UPDATE,
)
from .dispatcher import ClashDispatcher

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform for Clash."""
    _LOGGER.debug("Setting up sensor entities for Clash")
    dispatcher = entry.runtime_data.dispatcher

    sensors = [
        UploadSpeedSensor(dispatcher, entry),
        DownloadSpeedSensor(dispatcher, entry),
        UploadTotalSensor(dispatcher, entry),
        DownloadTotalSensor(dispatcher, entry),
        ActiveConnectionSensor(dispatcher, entry),
        MemoryUsageSensor(dispatcher, entry),
    ]
    async_add_entities(sensors)


class UploadSpeedSensor(BaseEntity, SensorEntity):
    """Implementation of an upload speed sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the upload speed sensor."""
        super().__init__(dispatcher, entry, SIGNAL_UPLOAD_SPEED_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-upload-speed"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "B/s"
        self._attr_suggested_unit_of_measurement = "kB/s"
        self._attr_suggested_display_precision = 0
        self._attr_icon = "mdi:upload"
        self._attr_translation_key = "upload_speed"

    @property
    def native_value(self) -> int | None:
        """Return the current upload speed."""
        return self.dispatcher.data.upload_speed


class DownloadSpeedSensor(BaseEntity, SensorEntity):
    """Implementation of a download speed sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the download speed sensor."""
        super().__init__(dispatcher, entry, SIGNAL_DOWNLOAD_SPEED_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-download-speed"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "B/s"
        self._attr_suggested_unit_of_measurement = "kB/s"
        self._attr_suggested_display_precision = 0
        self._attr_icon = "mdi:download"
        self._attr_translation_key = "download_speed"

    @property
    def native_value(self) -> int | None:
        """Return the current download speed."""
        return self.dispatcher.data.download_speed


class DownloadTotalSensor(BaseEntity, SensorEntity):
    """Implementation of a download total sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the download total traffic sensor."""
        super().__init__(dispatcher, entry, SIGNAL_DOWNLOAD_TOTAL_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-download-total"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "B"
        self._attr_suggested_unit_of_measurement = "GB"
        self._attr_suggested_display_precision = 2
        self._attr_icon = "mdi:download"
        self._attr_translation_key = "upload_total"

    @property
    def native_value(self) -> int | None:
        """Return the total download data."""
        return self.dispatcher.data.download_total


class UploadTotalSensor(BaseEntity, SensorEntity):
    """Implementation of an upload total traffic sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the upload total traffic sensor."""
        super().__init__(dispatcher, entry, SIGNAL_UPLOAD_TOTAL_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-upload-total"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "B"
        self._attr_suggested_unit_of_measurement = "GB"
        self._attr_suggested_display_precision = 2
        self._attr_icon = "mdi:upload"
        self._attr_translation_key = "upload_total"

    @property
    def native_value(self) -> int | None:
        """Return the total upload data."""
        return self.dispatcher.data.upload_total


class ActiveConnectionSensor(BaseEntity, SensorEntity):
    """Implementation of an active connection sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the active connection sensor."""
        super().__init__(dispatcher, entry, SIGNAL_ACTIVE_CONNECTIONS_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-active-connection"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 0
        self._attr_icon = "mdi:lan-connect"
        self._attr_translation_key = "active_connections"

    @property
    def native_value(self) -> int | None:
        """Return the number of active connections."""
        return self.dispatcher.data.active_connections


class MemoryUsageSensor(BaseEntity, SensorEntity):
    """Implementation of a memory usage sensor."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the memory usage sensor."""
        super().__init__(dispatcher, entry, SIGNAL_MEMORY_USAGE_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-memory-usage"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "B"
        self._attr_suggested_unit_of_measurement = "MB"
        self._attr_suggested_display_precision = 0
        self._attr_translation_key = "memory_usage"

    @property
    def native_value(self) -> int | None:
        """Return the total upload data."""
        return self.dispatcher.data.memory_usage


# class GroupSensor(BaseEntity, SensorEntity):
#     """Implementation of a memory sensor."""

#     def __init__(self, coordinator: ClashCoordinator, entity_data: dict) -> None:
#         super().__init__(coordinator, entity_data)

#     @property
#     def native_value(self) -> int | None:
#         return self.entity_data.get("state")
