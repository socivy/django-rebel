from requests import HTTPError

class RebelException(Exception):
    pass


class TargetMissing(RebelException):
    """
    Raise when send api is missing to, bcc or cc
    """


class RebelAPIError(HTTPError, RebelException):
    pass
