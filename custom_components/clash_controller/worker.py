"""Clash worker for fetching data."""

import asyncio
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry

from .api import ClashAPI
from .dispatcher import ClashDispatcher, ProxyGroup

_LOGGER = logging.getLogger(__name__)


class ClashWorker:
    """Class to fetch data."""

    fetching: bool
    api: ClashAPI
    dispatcher: ClashDispatcher

    def __init__(
        self, entry: ConfigEntry, api: ClashAPI, dispathcer: ClashDispatcher
    ) -> None:
        """Initialize clash worker."""
        self.fetching = False
        self.dispatcher = dispathcer
        self.api = api

    async def fetch_proxy_groups(self) -> None:
        """Worker to fetch proxy groups periodically."""
        while self.fetching:
            try:
                proxy_groups = {}
                response = await self.get_proxy_groups()
                for item in response.get("proxies", []):
                    if item.get("type") in [
                        "Selector",
                        "Fallback",
                        "URLTest",
                        "LoadBalance",
                    ]:
                        group = ProxyGroup()
                        group.name = item.get("name", "")
                        group.type = item.get("type", "")
                        group.options = item.get("all", [])
                        group.now = item.get("now", "")
                        proxy_groups[item["name"]] = group
                self.dispatcher.update_proxy_groups(proxy_groups)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching proxy groups: %s", e)
            await asyncio.sleep(30)

    async def fetch_configs(self) -> None:
        """Worker to fetch configurations periodically."""
        while self.fetching:
            try:
                response = await self.get_configs()
                mode = response.get("mode", "")
                self.dispatcher.update_mode(mode)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching configs: %s", e)
            await asyncio.sleep(30)

    async def fetch_connections(self) -> None:
        """Worker to fetch connections periodically."""
        while self.fetching:
            try:
                response = await self.get_connnections()
                upload_total = response.get("uploadTotal", 0)
                download_total = response.get("downloadTotal", 0)
                active_connections = len(response.get("connections", []))
                self.dispatcher.update_upload_total(upload_total)
                self.dispatcher.update_download_total(download_total)
                self.dispatcher.update_active_connections(active_connections)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching connections: %s", e)
            await asyncio.sleep(30)

    async def fetch_version(self) -> None:
        """Worker to fetch version information periodically."""
        while self.fetching:
            try:
                response = await self.get_version()
                manufacturer = "Clash"
                model = "standard"
                if response.get("meta"):
                    model = "Meta"
                version = response.get("version", "")
                self.dispatcher.update_device_info(manufacturer, model, version)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching version information: %s", e)
            await asyncio.sleep(30)

    async def fetch_traffic(self) -> None:
        """Worker to fetch traffic statistics periodically."""
        while self.fetching:
            try:
                async for response in self.get_traffic():
                    if not self.fetching:
                        break
                    upload_speed = response.get("up", 0)
                    download_speed = response.get("down", 0)
                    self.dispatcher.update_upload_speed(upload_speed)
                    self.dispatcher.update_download_speed(download_speed)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching traffic statistics: %s", e)
            await asyncio.sleep(5)

    async def fetch_memory(self) -> None:
        """Worker to fetch memory usage periodically."""
        while self.fetching:
            try:
                async for response in self.get_memory():
                    if not self.fetching:
                        break
                    memory_usage = response.get("inuse", 0)
                    self.dispatcher.update_memory_usage(memory_usage)
            except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
                _LOGGER.error("Error fetching memory usage: %s", e)
            await asyncio.sleep(5)

    def start_fetching(self) -> None:
        """Start fetching data from the API."""
        self.fetching = True
        _LOGGER.debug("Starting Clash API data fetching")
        hass = self.dispatcher.hass
        hass.loop.call_soon(asyncio.create_task, self.fetch_proxy_groups())
        hass.loop.call_soon(asyncio.create_task, self.fetch_configs())
        hass.loop.call_soon(asyncio.create_task, self.fetch_connections())
        hass.loop.call_soon(asyncio.create_task, self.fetch_version())
        hass.loop.call_soon(asyncio.create_task, self.fetch_traffic())
        hass.loop.call_soon(asyncio.create_task, self.fetch_memory())

    async def stop_fetching(self) -> None:
        """Stop fetching data from the API."""
        self.fetching = False
