"""The Ofen-Innovativ integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientConnectionError
from async_timeout import timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

from .api import OfenInnovativAPIClient
from .api.types import (
    IPStatus,
    FireplaceState,
    DateTimeInfo,
)


@dataclass
class OfenInnovativPollData:
    ip_status: IPStatus
    fireplace_state: FireplaceState
    system_datetime: DateTimeInfo

    @property
    def serial(self) -> str:
        return self.ip_status.mac_address.replace(':', '').upper()


class OfenInnovativDataUpdateCoordinator(DataUpdateCoordinator[OfenInnovativPollData]):
    """Class to manage the polling of the fireplace API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: OfenInnovativAPIClient,
    ) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=15),
        )
        self._api_client = api_client

    async def _async_update_data(self) -> OfenInnovativPollData:
        return OfenInnovativPollData(
            ip_status=await self._api_client.retrieve_ip_status(),
            fireplace_state=await self._api_client.retrieve_fireplace_state(),
            system_datetime=await self._api_client.retrieve_system_datetime(),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            manufacturer="Ofen-Innovativ",
            model="OI-",
            name="Ofen-Innovativ Fireplace",
            identifiers={("IntelliFire", f"{self.data.serial}]")},
            configuration_url=f"http://{self._api_client.host}/",
        )
