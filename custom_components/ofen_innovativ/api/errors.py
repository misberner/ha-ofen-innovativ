
class ResponseParseError(Exception):
    pass


class ResponseValueError(Exception):
    pass


class UnexpectedResponseDataType(ResponseValueError):
    pass
