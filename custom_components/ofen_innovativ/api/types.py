from datetime import datetime
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class IPStatus:
    mac_address: str


@dataclass
class FireplaceState:
    phase: int
    door: bool
    temperature: int
    shutter: int
    movement: bool
    burn_time_mins: int
    hood: int
    position: int
    alarm1: int
    alarm2: int

    DATA_TYPE: ClassVar[int] = 0x00

    @classmethod
    def parse(cls, untyped_payload: bytes) -> 'FireplaceState':
        if len(untyped_payload) < 10:
            raise ValueError(f'not enough bytes in payload: got {len(untyped_payload)}, expected at least 10 bytes')
        phase = int(untyped_payload[0])
        door = (phase >> 4) in {1, 3}
        phase = phase % 0x10
        temperature = int.from_bytes(untyped_payload[1:3], byteorder='big')
        shutter = int(untyped_payload[3])
        movement = False
        if shutter > 100:
            shutter -= 150
            movement = True

        burn_time_h = int(untyped_payload[4])
        burn_time_m = int(untyped_payload[5])
        burn_time_mins_total = burn_time_h * 60 + burn_time_m
        alarm1 = int(untyped_payload[6])
        hood = int(untyped_payload[7])
        alarm2 = int(untyped_payload[8])
        position = int(untyped_payload[9])

        return FireplaceState(
            phase=phase,
            door=door,
            temperature=temperature,
            shutter=shutter,
            movement=movement,
            burn_time_mins=burn_time_mins_total,
            hood=hood,
            position=position,
            alarm1=alarm1,
            alarm2=alarm2,
        )


@dataclass
class DateTimeInfo:
    datetime: datetime
    source: int

    DATA_TYPE: ClassVar[int] = 0x22

    @classmethod
    def parse(cls, untyped_payload: bytes) -> 'DateTimeInfo':
        if len(untyped_payload) != 5:
            raise ValueError(f'payload has unexpected length {len(untyped_payload)}, expected 5 bytes')
        year = int(untyped_payload[0])
        month = int(untyped_payload[1])
        datetime_source = 0
        if month > 0x20:
            datetime_source = 2
            month -= 0x20
        elif month > 0x10:
            datetime_source = 1
            month -= 0x10

        day = int(untyped_payload[2])
        hour = int(untyped_payload[3])
        minute = int(untyped_payload[4])

        system_datetime = datetime(year=2000 + year, month=month, day=day, hour=hour, minute=minute)

        return DateTimeInfo(
            datetime=system_datetime,
            source=datetime_source,
        )
