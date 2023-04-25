"""Config flow for IntelliFire integration."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict

from aiohttp import ClientConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.dhcp import DhcpServiceInfo
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, LOGGER
from .api import OfenInnovativAPIClient

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


@dataclass
class DiscoveredHostInfo:
    """Host info for discovery."""

    ip: str
    serial: str | None


async def validate_host_input(host: str) -> str:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    LOGGER.debug("Instantiating Ofen-Innovativ with host: [%s]", host)

    async with OfenInnovativAPIClient(fireplace_host=host) as api_client:
        ip_status = await api_client.retrieve_ip_status()

    LOGGER.debug("Found a fireplace: %s", ip_status.mac_address)
    # Return the serial number which will be used to calculate a unique ID for the device/sensors
    return ip_status.mac_address


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ofen-Innovativ."""

    VERSION = 1

    def __init__(self):
        """Initialize the Config Flow Handler."""
        self._host: str = ""

    async def _async_validate_ip_and_continue(self, host: str) -> FlowResult:
        """Validate local config and continue."""
        self._async_abort_entries_match({CONF_HOST: host})
        self._serial = (await validate_host_input(host)).replace(':', '').upper()
        self._host = host

        await self.async_set_unique_id(self._serial)
        return self.async_create_entry(
            title=f'Ofen-Innovativ Fireplace {self._serial}',
            data={CONF_HOST: host},
        )

    async def async_step_manual_device_entry(self, user_input=None):
        """Handle manual input of local IP configuration."""
        LOGGER.debug("STEP: manual_device_entry")
        errors = {}
        self._host = user_input.get(CONF_HOST) if user_input else None
        if user_input is not None:
            try:
                return await self._async_validate_ip_and_continue(self._host)
            except (ConnectionError, ClientConnectionError):
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="manual_device_entry",
            errors=errors,
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=self._host): str}),
        )

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Start the user flow."""

        return await self.async_step_manual_device_entry()
