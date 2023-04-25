"""Support for IntelliFire Binary Sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import List, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import OfenInnovativDataUpdateCoordinator, OfenInnovativPollData
from .const import DOMAIN
from .entity import OfenInnovativEntity


@dataclass
class OfenInnovativBinarySensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[OfenInnovativPollData], bool]
    icon_fn: Optional[Callable[[OfenInnovativPollData], str]] = None

    def dynamic_icon(self, data: OfenInnovativPollData):
        if self.icon_fn is not None:
            return self.icon_fn(data)
        return getattr(self, 'icon', '')


@dataclass
class OfenInnovativBinarySensorEntityDescription(
    BinarySensorEntityDescription, OfenInnovativBinarySensorRequiredKeysMixin,
):
    """Describes a binary sensor entity."""


OFEN_INNOVATIV_BINARY_SENSORS: List[OfenInnovativBinarySensorEntityDescription] = [
    OfenInnovativBinarySensorEntityDescription(
        key="door_open",  # This is the sensor name
        name="Door Open",  # This is the human readable name
        icon="mdi:door",
        value_fn=lambda data: data.fireplace_state.door,
    ),
    OfenInnovativBinarySensorEntityDescription(
        key="hood_switch_on",
        name="Hood Switch On",
        icon="mdi:fan-remove",
        value_fn=lambda data: data.fireplace_state.hood != 0,
    ),
    OfenInnovativBinarySensorEntityDescription(
        key="movement",
        name="Movement",
        value_fn=lambda data: data.fireplace_state.movement,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a IntelliFire On/Off Sensor."""
    coordinator: OfenInnovativDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        OfenInnovativBinarySensor(coordinator=coordinator, description=description)
        for description in OFEN_INNOVATIV_BINARY_SENSORS
    )


class OfenInnovativBinarySensor(OfenInnovativEntity, BinarySensorEntity):
    """Extends IntellifireEntity with Binary Sensor specific logic."""

    entity_description: OfenInnovativBinarySensorEntityDescription

    @property
    def is_on(self) -> bool:
        """Use this to get the correct value."""
        return self.entity_description.value_fn(self.coordinator.data)
