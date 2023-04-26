"""Platform for sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from typing import List, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, TIME_MINUTES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import OfenInnovativDataUpdateCoordinator, OfenInnovativPollData
from .entity import OfenInnovativEntity


@dataclass
class OfenInnovativSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Optional[Callable[[OfenInnovativPollData], int | str | datetime | None]] = None
    icon_fn: Optional[Callable[[OfenInnovativPollData], str]] = None

    def dynamic_icon(self, data: OfenInnovativPollData):
        if self.icon_fn is not None:
            return self.icon_fn(data)
        return getattr(self, 'icon', '')


@dataclass
class OfenInnovativSensorEntityDescription(
    OfenInnovativSensorRequiredKeysMixin,
    SensorEntityDescription,
):
    """Describes a sensor entity."""


OFEN_INNOVATIV_SENSORS: List[OfenInnovativSensorEntityDescription] = [
    OfenInnovativSensorEntityDescription(
        key="temperature",
        name="Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        value_fn=lambda data: data.fireplace_state.temperature,
    ),
    OfenInnovativSensorEntityDescription(
        key="shutter_state",
        name="Shutter State",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.fireplace_state.shutter,
    ),
    OfenInnovativSensorEntityDescription(
        key="system_time",
        name="System Time",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.system_datetime.datetime.astimezone(None),
    ),
    OfenInnovativSensorEntityDescription(
        key="burn_duration",
        name="Burn Duration",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=TIME_MINUTES,
        value_fn=lambda data: data.fireplace_state.burn_time_mins,
    ),
    OfenInnovativSensorEntityDescription(
        key="position",
        name="Position",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.fireplace_state.position,
    ),
    OfenInnovativSensorEntityDescription(
        key="phase",
        name="Phase",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.fireplace_state.phase,
        icon_fn=lambda data: 'mdi:fireplace-off' if data.fireplace_state.phase == 0 else 'mdi:fireplace'
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Define setup entry call."""

    coordinator: OfenInnovativDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OfenInnovativSensor(coordinator=coordinator, description=description)
        for description in OFEN_INNOVATIV_SENSORS
    )


class OfenInnovativSensor(OfenInnovativEntity, SensorEntity):
    """Extends OfenInnovativEntity with Sensor specific logic."""

    entity_description: OfenInnovativSensorEntityDescription

    @property
    def native_value(self) -> int | str | datetime | None:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def icon(self) -> str:
        return self.entity_description.dynamic_icon(self.coordinator.data)
