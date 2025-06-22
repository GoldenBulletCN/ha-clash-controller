"""Data coordinator for Clash Controller."""

from dataclasses import dataclass, field
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    SIGNAL_ACTIVE_CONNECTIONS_UPDATE,
    SIGNAL_DEVICE_INFO_UPDATE,
    SIGNAL_DOWNLOAD_SPEED_UPDATE,
    SIGNAL_DOWNLOAD_TOTAL_UPDATE,
    SIGNAL_MEMORY_USAGE_UPDATE,
    SIGNAL_MODE_UPDATE,
    SIGNAL_PROXY_GROUPS_UPDATE,
    SIGNAL_UPLOAD_SPEED_UPDATE,
    SIGNAL_UPLOAD_TOTAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


# class ClashControllerCoordinator(DataUpdateCoordinator):
#     """A coordinator to fetch data from the Clash API."""

#     device: Optional[DeviceInfo] = None

#     def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
#         """Initialize the Clash Controller coordinator."""
#         self.host = config_entry.data["api_url"]
#         self.token = config_entry.data["bearer_token"]
#         self.allow_unsafe = config_entry.data["allow_unsafe"]

#         self.poll_interval = config_entry.options.get(
#             CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
#         )
#         self.concurrent_connections = config_entry.options.get(
#             CONF_CONCURRENT_CONNECTIONS, DEFAULT_CONCURRENT_CONNECTIONS
#         )

#         super().__init__(
#             hass,
#             _LOGGER,
#             name=f"{DOMAIN} ({self.host})",
#             update_method=self._async_update_data,
#             update_interval=timedelta(seconds=self.poll_interval),
#         )

#         self.api = ClashAPIOld(
#             host=self.host, token=self.token, allow_unsafe=self.allow_unsafe
#         )
#         _LOGGER.debug("Clash API initialized for coordinator %s", self.name)

#     async def _get_device(self) -> DeviceInfo:
#         """Generate a device object."""
#         version_info = await self.api.get_version()
#         return DeviceInfo(
#             name="Clash Instance",
#             manufacturer="Clash",
#             model=version_info.get("meta"),
#             sw_version=version_info.get("version"),
#             identifiers={(DOMAIN, self.api.device_id)},
#         )

#     async def _async_update_data(self):
#         """Fetch data from API endpoint."""
#         response: dict[str, Any] = {}
#         is_connected = False
#         _LOGGER.debug("Start fetching data from Clash")

#         try:
#             is_connected = await self.api.connected(suppress_errors=False)
#         except Exception as err:
#             raise UpdateFailed(f"Error communicating with API: {err}") from err

#         if is_connected:
#             response = await self.api.fetch_data()
#             if not self.device:
#                 self.device = await self._get_device()

#         traffic = response.get("traffic", {})
#         connections = response.get("connections", {})
#         memory = response.get("memory", {})
#         proxies = response.get("proxies", {})
#         mode = response.get("configs", {})["mode"]

#         entity_data = [
#             {
#                 "name": "Upload Speed",
#                 "state": traffic.get("up"),
#                 "entity_type": "traffic_sensor",
#                 "icon": "mdi:arrow-up",
#                 "translation_key": "up_speed",
#             },
#             {
#                 "name": "Download Speed",
#                 "state": traffic.get("down"),
#                 "entity_type": "traffic_sensor",
#                 "icon": "mdi:arrow-down",
#                 "translation_key": "down_speed",
#             },
#             {
#                 "name": "Upload Traffic",
#                 "state": connections.get("uploadTotal"),
#                 "entity_type": "total_traffic_sensor",
#                 "icon": "mdi:tray-arrow-up",
#                 "translation_key": "up_traffic",
#             },
#             {
#                 "name": "Download Traffic",
#                 "state": connections.get("downloadTotal"),
#                 "entity_type": "total_traffic_sensor",
#                 "icon": "mdi:tray-arrow-down",
#                 "translation_key": "down_traffic",
#             },
#             {
#                 "name": "Memory Used",
#                 "state": memory.get("inuse"),
#                 "entity_type": "memory_sensor",
#                 "icon": "mdi:memory",
#                 "translation_key": "memory_used",
#             },
#             {
#                 "name": "Connection Number",
#                 "state": len(connections.get("connections", []) or []),
#                 "entity_type": "connection_sensor",
#                 "icon": "mdi:transit-connection",
#                 "translation_key": "connection_number",
#             },
#             {
#                 "name": "Flush FakeIP Cache",
#                 "entity_type": "fakeip_flush_button",
#                 "icon": "mdi:broom",
#                 "translation_key": "flush_cache",
#                 "action": {
#                     "method": self.api.async_request,
#                     "args": ("POST", "cache/fakeip/flush"),
#                 },
#             },
#         ]

#         entity_data.append(
#             {
#                 "name": "Mode",
#                 "state": mode,
#                 "entity_type": "mode_selector",
#                 "icon": "mdi:network-outline",
#                 "options": ["global", "rule", "direct"],
#                 "translation_key": "mode_selector",
#             }
#         )
#         group_selector_items = ["tfo", "type", "udp", "xudp", "alive", "history"]
#         group_sensor_items = group_selector_items + ["all"]

#         for item in proxies.get("proxies", {}).values():
#             if item.get("type") in ["Selector", "Fallback"]:
#                 entity_data.append(
#                     {
#                         "name": item.get("name"),
#                         "state": item.get("now"),
#                         "entity_type": "proxy_group_selector",
#                         "icon": "mdi:network-outline",
#                         "options": item.get("all"),
#                         "attributes": {
#                             k: item[k] for k in group_selector_items if k in item
#                         },
#                     }
#                 )
#             elif item.get("type") == "URLTest":
#                 entity_data.append(
#                     {
#                         "name": item.get("name"),
#                         "state": item.get("now"),
#                         "entity_type": "proxy_group_sensor",
#                         "icon": "mdi:network-outline",
#                         "attributes": {
#                             k: item[k] for k in group_sensor_items if k in item
#                         },
#                     }
#                 )

#         for item in entity_data:
#             item["unique_id"] = (
#                 f"{self.api.device_id}"
#                 f"_{item['entity_type']}"
#                 f"_{item['name'].lower().replace(' ', '_')}"
#             )

#         return entity_data

#     def get_data_by_name(self, name: str) -> dict | None:
#         """Retrieve data by name."""
#         return next((item for item in self.data if item["name"] == name), None)


########################################################################################


@dataclass
class ProxyGroup:
    """A class to represent a proxy group."""

    name: str = ""
    type: str = ""
    options: list[str] = field(default_factory=list)
    now: str = ""


@dataclass
class ClashData:
    """A class to represent Clash data."""

    mode: str = ""
    upload_speed: int = 0
    download_speed: int = 0
    upload_total: int = 0
    download_total: int = 0
    active_connections: int = 0
    memory_usage: int = 0
    proxy_groups: dict[str, ProxyGroup] = field(default_factory=dict)
    manufacturer: str = ""
    model: str = ""
    version: str = ""


class ClashDispatcher:
    """A coordinator to fetch data from the Clash API."""

    hass: HomeAssistant
    data: ClashData

    def update_mode(self, mode: str) -> None:
        """Update mode."""
        self.data.mode = mode
        async_dispatcher_send(self.hass, SIGNAL_MODE_UPDATE)

    def update_upload_speed(self, upload_speed: int) -> None:
        """Update upload speed."""
        self.data.upload_speed = upload_speed
        async_dispatcher_send(self.hass, SIGNAL_UPLOAD_SPEED_UPDATE)

    def update_download_speed(self, download_speed: int) -> None:
        """Update download speed."""
        self.data.download_speed = download_speed
        async_dispatcher_send(self.hass, SIGNAL_DOWNLOAD_SPEED_UPDATE)

    def update_upload_total(self, upload_total: int) -> None:
        """Update total upload traffic."""
        self.data.upload_total = upload_total
        async_dispatcher_send(self.hass, SIGNAL_UPLOAD_TOTAL_UPDATE)

    def update_download_total(self, download_total: int) -> None:
        """Update total download traffic."""
        self.data.download_total = download_total
        async_dispatcher_send(self.hass, SIGNAL_DOWNLOAD_TOTAL_UPDATE)

    def update_active_connections(self, active_connections: int) -> None:
        """Update number of active connections."""
        self.data.active_connections = active_connections
        async_dispatcher_send(self.hass, SIGNAL_ACTIVE_CONNECTIONS_UPDATE)

    def update_memory_usage(self, memory_usage: int) -> None:
        """Update memory usage."""
        self.data.memory_usage = memory_usage
        async_dispatcher_send(self.hass, SIGNAL_MEMORY_USAGE_UPDATE)

    def update_proxy_groups(self, proxy_groups: dict[str, ProxyGroup]) -> None:
        """Update proxy groups."""
        self.data.proxy_groups = proxy_groups
        async_dispatcher_send(self.hass, SIGNAL_PROXY_GROUPS_UPDATE)

    def update_device_info(self, manufacturer: str, model: str, version: str) -> None:
        """Update device information."""
        self.data.manufacturer = manufacturer
        self.data.model = model
        self.data.version = version
        async_dispatcher_send(self.hass, SIGNAL_DEVICE_INFO_UPDATE)

    def refresh_all(self) -> None:
        """Update all data."""
        async_dispatcher_send(self.hass, SIGNAL_MODE_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_UPLOAD_SPEED_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_DOWNLOAD_SPEED_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_UPLOAD_TOTAL_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_DOWNLOAD_TOTAL_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_ACTIVE_CONNECTIONS_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_MEMORY_USAGE_UPDATE)
        async_dispatcher_send(self.hass, SIGNAL_PROXY_GROUPS_UPDATE)

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Clash Coordinator."""
        self.hass = hass
        self.data = ClashData()


########################################################################################
# async def _async_update_data(self) -> dict[str, Any]:
#     """Fetch data from API endpoint."""

#     # Get proxiy_groups
#     proxy_groups = {}
#     proxies = await self.api.get_proxy_groups()
#     for item in proxies.get("proxies", {}):
#         if item.get("type") in ["Selector", "Fallback", "URLTest", "LoadBalance"]:
#             proxy_groups[item["name"]] = {
#                 "options": item.get("all", []),
#                 "now": item.get("now", None),
#             }
#     # Get mode
#     configs = await self.api.get_configs()
#     mode = configs.get("mode", None)

#     # Get traffic
#     traffic_list = await self.api.get_traffic(1)
#     traffic = traffic_list[0] if traffic_list else {}
#     upload_speed = traffic.get("up", 0)
#     download_speed = traffic.get("down", 0)
#     connections = await self.api.get_connnections()
#     upload_total = connections.get("uploadTotal", 0)
#     download_total = connections.get("downloadTotal", 0)

#     # Get memory usage
#     memory_list = await self.api.get_memory(2)
#     memory_usage = memory_list[1].get("inuse", 0) if len(memory_list) > 1 else 0

#     return {
#         "proxy_groups": proxy_groups,
#         "mode": mode,
#         "upload_speed": upload_speed,
#         "download_speed": download_speed,
#         "upload_total": upload_total,
#         "download_total": download_total,
#         "memory_usage": memory_usage,
#     }
