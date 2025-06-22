"""Base entity for Clash."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .dispatcher import ClashDispatcher


class BaseEntity(Entity):
    """Base entity for Clash Controller using dispatcher."""

    _unsub_dispatcher: Callable[[], None] | None
    dispatcher: ClashDispatcher
    _signal: str

    def __init__(
        self, dispatcher: ClashDispatcher, entry: ConfigEntry, signal: str
    ) -> None:
        """Initialize the base entity."""
        super().__init__()
        self._unsub_dispatcher = None
        self.dispatcher = dispatcher
        self._signal = signal
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._attr_has_entity_name = True

    async def async_added_to_hass(self) -> None:
        """Register dispatcher to update entity when data changes."""
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass,
            self._signal,
            self._handle_dispatcher_update,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister dispatcher."""
        if self._unsub_dispatcher is not None:
            self._unsub_dispatcher()
            self._unsub_dispatcher = None

    async def _handle_dispatcher_update(self) -> None:
        """Handle dispatcher signal to update entity state."""
        self.async_write_ha_state()


class BaseManager(ABC):
    """Base manager for Clash entities."""

    _unsub_dispatcher: Callable[[], None] | None
    dispatcher: ClashDispatcher
    _signal: str
    hass: HomeAssistant | None
    entry: ConfigEntry | None

    def __init__(
        self, dispatcher: ClashDispatcher, entry: ConfigEntry, signal: str
    ) -> None:
        """Initialize the base manager."""
        self._unsub_dispatcher = None
        self.dispatcher = dispatcher
        self._signal = signal
        self.entry = entry
        self.hass = None

    def register_manager(self, hass: HomeAssistant) -> None:
        """Register the manager with Home Assistant."""
        self.hass = hass
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass,
            self._signal,
            self._handle_dispatcher_update,
        )
        self.entry.async_on_unload(self._unsub_dispatcher)

    @abstractmethod
    async def _handle_dispatcher_update(self) -> None:
        """Handle dispatcher update signal."""
