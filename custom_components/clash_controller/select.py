"""Select platform for Clash Controller."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RuntimeData
from .base import BaseEntity, BaseManager
from .const import SIGNAL_MODE_UPDATE, SIGNAL_PROXY_GROUPS_UPDATE
from .dispatcher import ClashDispatcher

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RuntimeData],
    async_add_entities: AddEntitiesCallback,
):
    """Set up the select platform for Clash."""
    _LOGGER.debug("Setting up select entities for Clash")
    dispatcher = entry.runtime_data.dispatcher

    # Add the mode select entity
    async_add_entities([ModeSelect(dispatcher, entry)])

    # Initilize and register proxy group select manager
    manager = ProxyGroupSelectManager(dispatcher, entry, async_add_entities)
    manager.register_manager(hass)


class ProxyGroupSelect(BaseEntity, SelectEntity):
    """Implementation of a proxy group select entity."""

    def __init__(
        self,
        dispatcher: ClashDispatcher,
        entry: ConfigEntry,
        group_name: str,
    ) -> None:
        """Initialize the group select entity."""
        super().__init__(dispatcher, entry, SIGNAL_PROXY_GROUPS_UPDATE)
        self._attr_name = group_name
        self._attr_unique_id = f"{entry.entry_id}-proxygroup-{group_name}"
        self._attr_icon = "mdi:network-outline"
        # No Translation Key for Proxy Group Select
        self._attr_translation_key = None

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option for the proxy group."""
        group = self.dispatcher.data.proxy_groups.get(self._attr_name)
        return group.now if group is not None else None

    @property
    def options(self) -> list[str] | None:
        """Return the available options for the proxy group."""
        group = self.dispatcher.data.proxy_groups.get(self._attr_name)
        return group.options if group is not None else None

    # async def async_select_option(self, option: str) -> None:
    #     """Change the selected option for the proxy group."""
    #     group = self._attr_name
    #     try:
    #         await self.coordinator.api.async_request(
    #             "PUT", f"proxies/{group}", json_data={"name": option}
    #         )
    #     except Exception as err:
    #         raise HomeAssistantError(
    #             f"Failed to set proxy group {group} to {option}."
    #         ) from err
    #     self.coordinator.data["proxy_groups"][self._attr_name]["now"] = option
    #     self._attr_current_option = option
    #     self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Raise NotImplementedError; use async_select_option instead."""
        raise NotImplementedError("Use async_select_option instead of select_option")


class ProxyGroupSelectManager(BaseManager):
    """Manager for proxy group select entities."""

    proxy_groups: list[ProxyGroupSelect]
    async_add_entities: AddEntitiesCallback

    def __init__(
        self,
        dispatcher: ClashDispatcher,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the manager."""
        super().__init__(dispatcher, entry, SIGNAL_PROXY_GROUPS_UPDATE)
        self.proxy_groups = []
        self.async_add_entities = async_add_entities

    async def _handle_dispatcher_update(self) -> None:
        """Handle dispatcher signal to update proxy group entities."""
        existing_names = {group.name for group in self.proxy_groups}
        current_names = {
            group.name
            for group in self.dispatcher.data.proxy_groups.values()
            if group.type == "Selector"
        }
        set(self.dispatcher.data.proxy_groups.keys())

        new_names = current_names - existing_names
        removed_names = existing_names - current_names

        # Remove entities for any removed proxy groups
        if removed_names:
            for group in list(self.proxy_groups):
                if group.name in removed_names:
                    self.dispatcher.hass.async_create_task(group.async_remove())
                    self.proxy_groups.remove(group)
            _LOGGER.info("Proxy groups removed: %s", removed_names)

        # Add new entities for any new proxy groups
        if new_names:
            _LOGGER.info("New proxy groups detected: %s", new_names)
            new_proxy_groups = [
                ProxyGroupSelect(self.dispatcher, self.entry, name)
                for name in new_names
            ]
            self.async_add_entities(new_proxy_groups)
            self.proxy_groups.extend(new_proxy_groups)


class ModeSelect(BaseEntity, SelectEntity):
    """Implementation of a mode select entity."""

    def __init__(self, dispatcher: ClashDispatcher, entry: ConfigEntry) -> None:
        """Initialize the mode select entity."""
        super().__init__(dispatcher, entry, SIGNAL_MODE_UPDATE)
        self._attr_unique_id = f"{entry.entry_id}-mode"

        self._attr_icon = "mdi:format-list-bulleted-type"
        self._attr_options = ["rule", "global", "direct"]
        self._attr_translation_key = "mode_selector"

    @property
    def current_option(self) -> str | None:
        """Return the currently selected mode."""
        return self.dispatcher.data.mode

    # async def async_select_option(self, option: str) -> None:
    #     """Change the proxy mode."""
    #     try:
    #         await self.coordinator.api.async_request(
    #             "PATCH", "configs", json_data={"mode": option}
    #         )
    #     except Exception as err:
    #         raise HomeAssistantError(f"Failed to set mode to {option}.") from err
    #     self.coordinator.data["mode"] = option
    #     self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Raise NotImplementedError; use async_select_option instead."""
        raise NotImplementedError("Use async_select_option instead of select_option")
