from requests.exceptions import HTTPError, ConnectionError

class RebelException(Exception):
    pass


class TargetMissing(RebelException):
    """
    Raise when send api is missing to, bcc or cc
    """


class RebelAPIError(ConnectionError, HTTPError, RebelException):
    pass
