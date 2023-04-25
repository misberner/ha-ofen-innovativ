from __future__ import annotations

from aiohttp import ClientConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    Platform,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, LOGGER
from .api import OfenInnovativAPIClient
from .coordinator import OfenInnovativDataUpdateCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IntelliFire from a config entry."""
    LOGGER.debug("Setting up config entry: %s", entry.unique_id)

    if CONF_HOST not in entry.data:
        raise ConfigEntryAuthFailed

    api_client = OfenInnovativAPIClient(entry.data[CONF_HOST])

    # Define the update coordinator
    coordinator = OfenInnovativDataUpdateCoordinator(
        hass=hass,
        api_client=api_client,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
