from __future__ import annotations

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OfenInnovativDataUpdateCoordinator


class OfenInnovativEntity(CoordinatorEntity[OfenInnovativDataUpdateCoordinator]):
    """Define a generic class for Ofen-Innovativ entities."""

    _attr_attribution = "Data provided by unpublished Ofen-Innovativ API"

    def __init__(
        self,
        coordinator: OfenInnovativDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Class initializer."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        # Set the Display name the User will see
        self._attr_name = f"Fireplace {description.name}"
        self._attr_unique_id = f"{DOMAIN}-{coordinator.data.serial}-{description.key}"
        # Configure the Device Info
        self._attr_device_info = self.coordinator.device_info
