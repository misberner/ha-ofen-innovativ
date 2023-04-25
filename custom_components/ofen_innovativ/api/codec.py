_HEADER = b'\xaa\xcc\x33\x55'


def _pack_data(payload: bytes) -> bytes:
    packed_data = _HEADER
    payload_len = len(payload)
    if payload_len >= 0xff:
        packed_data += b'\xff'
        payload_len -= 0xff
    if payload_len >= 0xff:
        raise PayloadTooBigError(f'payload with {len(payload)} bytes is too long')
    packed_data += payload_len.to_bytes(1, byteorder='little')
    packed_data += payload
    checksum = _calc_checksum(payload)
    packed_data += checksum.to_bytes(2, byteorder='little')
    return packed_data


def _unpack_data(packed: bytes) -> bytes:
    if not packed.startswith(_HEADER):
        raise MissingHeaderError('data does not start with magic header')
    packed = packed[4:]

    payload_len = int(packed[0])
    packed = packed[1:]
    if payload_len == 0xff:
        payload_len += int(packed[0])
        packed = packed[1:]

    payload = packed[:-2]
    if len(payload) != payload_len:
        raise PayloadLengthMismatchError(f'message header indicated {payload_len} bytes of payload data, but ' +
                                         f'actual payload is {len(payload)} bytes')

    calced_checksum = _calc_checksum(payload)
    claimed_checksum = int.from_bytes(packed[-2:], byteorder='little')
    if calced_checksum != claimed_checksum:
        raise ChecksumValidationError(f'checksum mismatch: {calced_checksum:#x} vs. {claimed_checksum:#x}')

    return payload


def format_message(payload: bytes) -> str:
    return _pack_data(payload).hex()


def parse_message(message: str) -> bytes:
    return _unpack_data(bytes.fromhex(message))


def _calc_checksum(data: bytes) -> int:
    return sum(data) % 0x10000


class MissingHeaderError(BaseException):
    pass


class PayloadTooBigError(BaseException):
    pass


class ChecksumValidationError(BaseException):
    pass


class PayloadLengthMismatchError(BaseException):
    pass
