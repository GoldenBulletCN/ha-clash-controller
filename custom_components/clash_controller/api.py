"""Clash API interaction module."""

from collections.abc import AsyncGenerator
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.util.json import json_loads

from .dispatcher import ClashDispatcher

_LOGGER = logging.getLogger(__name__)


class ClashAPI:
    """Class to handle Clash API interactions."""

    base_url: str
    secret: str
    allow_insecure: bool

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize ClashAPI."""
        # self.base_url = entry.data["api_url"]
        # self.secret = entry.data["secret"]
        # self.allow_insecure = entry.data["allow_insecure"]
        # self.base_url = "http://192.168.50.6:9090"
        self.base_url = "http://10.213.1.9:9090"
        self.secret = ""
        self.allow_insecure = True
        timeout = aiohttp.ClientTimeout(total=0, sock_read=10, sock_connect=10)
        connector = aiohttp.TCPConnector(verify_ssl=not self.allow_insecure)
        if self.secret:
            headers = {"Authorization": f"Bearer {self.secret}"}
        else:
            headers = {}
        self.session = aiohttp.ClientSession(
            connector=connector, headers=headers, timeout=timeout
        )

    async def get_proxy_groups(self) -> dict:
        """Fetch proxy groups from the Clash API."""
        async with self.session.get(f"{self.base_url}/group") as response:
            response.raise_for_status()
            return await response.json()

    async def get_configs(self) -> dict:
        """Fetch configurations from the Clash API."""
        async with self.session.get(f"{self.base_url}/configs") as response:
            response.raise_for_status()
            return await response.json()

    async def get_version(self) -> dict:
        """Fetch the version information from the Clash API."""
        async with self.session.get(f"{self.base_url}/version") as response:
            response.raise_for_status()
            return await response.json()

    async def get_connnections(self) -> dict:
        """Fetch current connections from the Clash API."""
        async with self.session.get(f"{self.base_url}/connections") as response:
            response.raise_for_status()
            return await response.json()

    async def get_traffic(self) -> AsyncGenerator[dict]:
        """Fetch traffic statistics from the Clash API."""
        async with self.session.get(f"{self.base_url}/traffic") as response:
            response.raise_for_status()
            encoding = response.charset or "utf-8"
            async for line in response.content:
                if not line:
                    continue
                try:
                    yield json_loads(line.decode(encoding))
                except (UnicodeDecodeError, ValueError) as e:
                    _LOGGER.warning("Failed to parse stream line: %s", e)

    async def get_memory(self) -> AsyncGenerator[dict]:
        """Fetch memory usage from the Clash API."""
        async with self.session.get(f"{self.base_url}/memory") as response:
            response.raise_for_status()
            encoding = response.charset or "utf-8"
            async for line in response.content:
                if not line:
                    continue
                try:
                    yield json_loads(line.decode(encoding))
                except (UnicodeDecodeError, ValueError) as e:
                    _LOGGER.warning("Failed to parse stream line: %s", e)

    async def check_connection(self) -> bool:
        """Check if the API is reachable."""
        try:
            result = await self.get_version()
        except (aiohttp.ClientError, aiohttp.TimeoutError) as e:
            _LOGGER.error("Error connecting to Clash API: %s", e)
            return False
        else:
            _LOGGER.debug("Clash API version: %s", result.get("version"))
            return True

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()
