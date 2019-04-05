from requests.exceptions import HTTPError


class RebelException(Exception):
    pass


class TargetMissing(RebelException):
    """
    Raise when send api is missing to, bcc or cc
    """


class RebelAPIError(HTTPError, RebelException):
    pass


class RebelConnectionError(RebelException):
    pass


class RebelNotValidAddress(RebelAPIError):
    """
    Raises when mailgun returns 'to', 'bcc' or 'cc' parameter is not valid
    """
