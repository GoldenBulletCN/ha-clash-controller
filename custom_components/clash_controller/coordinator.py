"""Data coordinator for Clash Controller."""

from datetime import timedelta
import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClashAPI
from .const import (
    CONF_CONCURRENT_CONNECTIONS,
    DEFAULT_CONCURRENT_CONNECTIONS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ClashControllerCoordinator(DataUpdateCoordinator):
    """A coordinator to fetch data from the Clash API."""

    device: Optional[DeviceInfo] = None

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the Clash Controller coordinator."""
        self.host = config_entry.data["api_url"]
        self.token = config_entry.data["bearer_token"]
        self.allow_unsafe = config_entry.data["allow_unsafe"]

        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        self.concurrent_connections = config_entry.options.get(
            CONF_CONCURRENT_CONNECTIONS, DEFAULT_CONCURRENT_CONNECTIONS
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({self.host})",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=self.poll_interval),
        )

        self.api = ClashAPI(
            host=self.host, token=self.token, allow_unsafe=self.allow_unsafe
        )
        _LOGGER.debug(f"Clash API initialized for coordinator {self.name}")

    async def _get_device(self) -> DeviceInfo:
        """Generate a device object."""
        version_info = await self.api.get_version()
        return DeviceInfo(
            name="Clash Instance",
            manufacturer="Clash",
            model=version_info.get("meta"),
            sw_version=version_info.get("version"),
            identifiers={(DOMAIN, self.api.device_id)},
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        response: dict[str, Any] = {}
        is_connected = False
        _LOGGER.debug("Start fetching data from Clash")

        try:
            is_connected = await self.api.connected(suppress_errors=False)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        if is_connected:
            response = await self.api.fetch_data()
            if not self.device:
                self.device = await self._get_device()

        traffic = response.get("traffic", {})
        connections = response.get("connections", {})
        memory = response.get("memory", {})
        proxies = response.get("proxies", {})
        mode = response.get("configs", {})["mode"]

        entity_data = [
            {
                "name": "Upload Speed",
                "state": traffic.get("up"),
                "entity_type": "traffic_sensor",
                "icon": "mdi:arrow-up",
                "translation_key": "up_speed",
            },
            {
                "name": "Download Speed",
                "state": traffic.get("down"),
                "entity_type": "traffic_sensor",
                "icon": "mdi:arrow-down",
                "translation_key": "down_speed",
            },
            {
                "name": "Upload Traffic",
                "state": connections.get("uploadTotal"),
                "entity_type": "total_traffic_sensor",
                "icon": "mdi:tray-arrow-up",
                "translation_key": "up_traffic",
            },
            {
                "name": "Download Traffic",
                "state": connections.get("downloadTotal"),
                "entity_type": "total_traffic_sensor",
                "icon": "mdi:tray-arrow-down",
                "translation_key": "down_traffic",
            },
            {
                "name": "Memory Used",
                "state": memory.get("inuse"),
                "entity_type": "memory_sensor",
                "icon": "mdi:memory",
                "translation_key": "memory_used",
            },
            {
                "name": "Connection Number",
                "state": len(connections.get("connections", []) or []),
                "entity_type": "connection_sensor",
                "icon": "mdi:transit-connection",
                "translation_key": "connection_number",
            },
            {
                "name": "Flush FakeIP Cache",
                "entity_type": "fakeip_flush_button",
                "icon": "mdi:broom",
                "translation_key": "flush_cache",
                "action": {
                    "method": self.api.async_request,
                    "args": ("POST", "cache/fakeip/flush"),
                },
            },
        ]

        entity_data.append(
            {
                "name": "Mode",
                "state": mode,
                "entity_type": "mode_selector",
                "icon": "mdi:network-outline",
                "options": ["global", "rule", "direct"],
                "translation_key": "mode_selector",
            }
        )
        group_selector_items = ["tfo", "type", "udp", "xudp", "alive", "history"]
        group_sensor_items = group_selector_items + ["all"]

        for item in proxies.get("proxies", {}).values():
            if item.get("type") in ["Selector", "Fallback"]:
                entity_data.append(
                    {
                        "name": item.get("name"),
                        "state": item.get("now"),
                        "entity_type": "proxy_group_selector",
                        "icon": "mdi:network-outline",
                        "options": item.get("all"),
                        "attributes": {
                            k: item[k] for k in group_selector_items if k in item
                        },
                    }
                )
            elif item.get("type") == "URLTest":
                entity_data.append(
                    {
                        "name": item.get("name"),
                        "state": item.get("now"),
                        "entity_type": "proxy_group_sensor",
                        "icon": "mdi:network-outline",
                        "attributes": {
                            k: item[k] for k in group_sensor_items if k in item
                        },
                    }
                )

        for item in entity_data:
            item["unique_id"] = (
                f"{self.api.device_id}"
                f"_{item['entity_type']}"
                f"_{item['name'].lower().replace(' ', '_')}"
            )

        return entity_data

    def get_data_by_name(self, name: str) -> dict | None:
        """Retrieve data by name."""
        return next((item for item in self.data if item["name"] == name), None)
