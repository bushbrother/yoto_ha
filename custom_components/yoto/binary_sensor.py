"""Sensor for Yoto integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.binary_sensor import (
    # BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class YotoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes custom binary sensor entities."""

    is_on: Callable[[YotoPlayer], bool] | None = None
    on_icon: str | None = None
    off_icon: str | None = None


SENSOR_DESCRIPTIONS: Final[tuple[YotoBinarySensorEntityDescription, ...]] = (
    YotoBinarySensorEntityDescription(
        key="online",
        name="Online",
        is_on=lambda player: player.online,
        # on_icon="mdi:engine",
        # off_icon="mdi:engine-off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary_sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities: list[YotoBinarySensor] = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in SENSOR_DESCRIPTIONS:
            if getattr(player, description.key, None) is not None:
                entities.append(YotoBinarySensor(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoBinarySensor(BinarySensorEntity, YotoEntity):
    """Yoto binary sensor class."""

    def __init__(
        self,
        coordinator: YotoDataUpdateCoordinator,
        description: YotoBinarySensorEntityDescription,
        player: YotoPlayer,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self.entity_description: YotoBinarySensorEntityDescription = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"
        self._attr_name = f"{player.name} {description.name}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.is_on is not None:
            return self.entity_description.is_on(self.player)
        return None

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if (
            self.entity_description.on_icon == self.entity_description.off_icon
        ) is None:
            return BinarySensorEntity.icon
        return (
            self.entity_description.on_icon
            if self.is_on
            else self.entity_description.off_icon
        )
