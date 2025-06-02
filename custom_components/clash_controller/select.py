"""Select platform for Clash Controller."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RuntimeData
from .const import DOMAIN
from .coordinator import ClashCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _: HomeAssistant,
    entry: ConfigEntry[RuntimeData],
    async_add_entities: AddEntitiesCallback,
):
    """Set up the select platform for Clash Controller."""
    _LOGGER.debug("Setting up select entities for Clash Controller")
    coordinator = entry.runtime_data.coordinator

    # Add entities for each proxy group
    # proxy_groups = [
    #     GroupSelect(coordinator, entry, group["name"])
    #     for group in coordinator.data.get("proxy_groups", [])
    # ]
    # async_add_entities(proxy_groups)

    # Add the mode select entity
    async_add_entities([ModeSelect(coordinator, entry)])

    # Initialize a list to keep track of proxy group entities
    proxy_groups: list[GroupSelect] = []

    async def _update_proxy_groups():
        """Update proxy groups based on coordinator data."""
        existing_names = {group.name for group in proxy_groups}
        current_names = set(coordinator.data.get("proxy_groups", {}))

        new_names = current_names - existing_names
        removed_names = existing_names - current_names

        # Remove entities for any removed proxy groups
        if removed_names:
            for group in list(proxy_groups):
                if group.name in removed_names:
                    await group.async_remove()
                    proxy_groups.remove(group)
            _LOGGER.info("Proxy groups removed: %s", removed_names)

        # Add new entities for any new proxy groups
        if new_names:
            _LOGGER.info("New proxy groups detected: %s", new_names)
            new_proxy_groups = [
                GroupSelect(coordinator, entry, name) for name in new_names
            ]
            async_add_entities(new_proxy_groups)
            proxy_groups.extend(new_proxy_groups)

    # Initial update of proxy groups
    await _update_proxy_groups()

    # Register a listener to update proxy groups when coordinator data changes
    coordinator.async_add_listener(_update_proxy_groups)


# class SelectEntityBase(BaseEntity, SelectEntity):
#     """Base select entity class."""

#     def __init__(
#         self, coordinator: ClashControllerCoordinator, entity_data: dict
#     ) -> None:
#         super().__init__(coordinator, entity_data)

#     @property
#     def current_option(self) -> str | None:
#         return self.entity_data.get("state")

#     @property
#     def options(self) -> dict | None:
#         return self.entity_data.get("options")


class GroupSelect(CoordinatorEntity, SelectEntity):
    """Implementation of a proxy group select entity."""

    def __init__(
        self,
        coordinator: ClashCoordinator,
        entry: ConfigEntry[RuntimeData],
        group_name: str,
    ) -> None:
        """Initialize the group select entity."""
        self._attr_name = group_name
        self._attr_unique_id = f"{entry.entry_id}-proxygroup-{group_name}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._attr_icon = "mdi:network-outline"
        # No Translation Key for Group Select
        self._attr_translation_key = None
        super().__init__(coordinator)

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option for the proxy group."""
        return (
            self.coordinator.data.get("proxy_groups", {})
            .get(self._attr_name, {})
            .get("now", None)
        )

    @property
    def options(self) -> list[str] | None:
        """Return the available options for the proxy group."""
        return (
            self.coordinator.data.get("proxy_groups", {})
            .get(self._attr_name, {})
            .get("all", None)
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option for the proxy group."""
        group = self._attr_name
        try:
            await self.coordinator.api.async_request(
                "PUT", f"proxies/{group}", json_data={"name": option}
            )
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to set proxy group {group} to {option}."
            ) from err
        self.coordinator.data["proxy_groups"][self._attr_name]["now"] = option
        self._attr_current_option = option
        self.async_write_ha_state()

    def select_option(self, _: str) -> None:
        """Raise error as synchronous fallback is not implemented."""
        raise NotImplementedError(
            "GrouopSelect entity only supports async_select_option."
        )


class ModeSelect(CoordinatorEntity, SelectEntity):
    """Implementation of a mode select."""

    def __init__(
        self, coordinator: ClashCoordinator, entry: ConfigEntry[RuntimeData]
    ) -> None:
        """Initialize the mode select entity."""
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}-mode"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._attr_icon = "mdi:format-list-bulleted-type"
        self._attr_options = ["rule", "global", "direct"]
        self._attr_translation_key = "mode_selector"
        super().__init__(coordinator)

    @property
    def current_option(self) -> str | None:
        """Return the currently selected mode."""
        return self.coordinator.data.get("mode", None)

    async def async_select_option(self, option: str) -> None:
        """Change the proxy mode."""
        try:
            await self.coordinator.api.async_request(
                "PATCH", "configs", json_data={"mode": option}
            )
        except Exception as err:
            raise HomeAssistantError(f"Failed to set mode to {option}.") from err
        self.coordinator.data["mode"] = option
        self.async_write_ha_state()

    def select_option(self, _: str) -> None:
        """Raise error as synchronous fallback is not implemented."""
        raise NotImplementedError(
            "ModeSelect entity only supports async_select_option."
        )
