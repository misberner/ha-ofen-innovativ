import xml.etree.ElementTree as ET
from aiohttp import ClientSession
from datetime import datetime
from typing import Optional

from . import codec
from .types import (
    IPStatus,
    FireplaceState,
    DateTimeInfo,
)
from .errors import (
    ResponseParseError,
    ResponseValueError,
    UnexpectedResponseDataType,
)


class OfenInnovativAPIClient:
    _host: str
    _session: Optional[ClientSession]

    def __init__(self, fireplace_host):
        self._host = fireplace_host
        self._session = ClientSession(f'http://{fireplace_host}')

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> 'OfenInnovativAPIClient':
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()

    @property
    def host(self):
        return self._host

    async def retrieve_ip_status(self):
        async with self._session.post('/export/status', data='optionalGroupList=Interface:wlan0') as resp:
            resp.raise_for_status()
            resp_bytes = await resp.read()
        root_elem = ET.XML(resp_bytes)
        mac_addr = None
        if root_elem.tag != 'statusrecord':
            raise ResponseParseError(f'expected root element of response to have tag statusrecord, not {root_elem.tag}')
        for sg in root_elem:
            if mac_addr is not None:
                break
            if sg.tag != 'statusgroup' or sg.get('name') != 'Interface' or sg.get('instance') != 'wlan0':
                continue
            for si in sg:
                if si.tag != 'statusitem' or si.get('name') != 'MAC Address':
                    continue
                mac_addr = si.findtext('value')
                break

        if mac_addr is None:
            raise ResponseValueError('response contained no MAC address')

        return IPStatus(mac_address=mac_addr)

    async def retrieve_fireplace_state(self) -> FireplaceState:
        return await self._retrieve_state(FireplaceState, m=500)

    async def retrieve_system_datetime(self) -> DateTimeInfo:
        return await self._retrieve_state(DateTimeInfo, m=300)

    async def set_system_datetime(self, to: datetime):
        yy = to.year - 2000
        if yy < 0 or yy > 0xff:
            raise ValueError(f'year {to.year} is invalid')
        payload = b'\x23'  # set date time
        payload += yy.to_bytes(1, byteorder='little')
        payload += to.month.to_bytes(1, byteorder='little')
        payload += to.day.to_bytes(1, byteorder='little')
        payload += to.hour.to_bytes(1, byteorder='little')
        payload += to.minute.to_bytes(1, byteorder='little')
        return await self._post_status_action_bytes(payload, m=300)

    async def _retrieve_state(self, state_type, n=None, m=None, t=None):
        data_type = state_type.DATA_TYPE
        resp_payload = await self._post_status_action_bytes(data_type.to_bytes(1, byteorder='little'), n=n, m=m, t=t)
        if resp_payload[0] != data_type:
            raise UnexpectedResponseDataType(f'unexpected response data type {resp_payload[0]:#x}, expected {data_type:#x}')
        return state_type.parse(resp_payload[1:])

    async def _post_status_action_bytes(self, payload: bytes, line=1, n=None, m=None, t=None) -> bytes:
        message = codec.format_message(payload)
        resp_message = await self._post_status_action_raw(message, line=line, n=n, m=m, t=t)
        return codec.parse_message(resp_message)

    async def _post_status_action_raw(self, message: str, line=1, n=None, m=None, t=None) -> str:
        post_msg = f'group=Line&optionalGroupInstance={line}&action=Command '
        if n is not None:
            post_msg += f'n={n} '
        if m is not None:
            post_msg += f'm={m} '
        if t is not None:
            post_msg += f't={t} '
        post_msg += message

        async with self._session.post('/action/status', data=post_msg) as resp:
            resp.raise_for_status()
            resp_bytes = await resp.read()

        root_elem = ET.XML(resp_bytes)
        if root_elem.tag != 'function':
            raise ResponseParseError(f'expected root element of response to have tag function, not {root_elem.tag}')
        ret = root_elem.find('return')
        if ret is None:
            raise ResponseParseError(f'response did not contain a function return')
        if (res := ret.findtext('result')) != 'Succeeded':
            raise ResponseValueError(f'non-successful function result: {res}')

        msg = ret.findtext('message')

        return msg
