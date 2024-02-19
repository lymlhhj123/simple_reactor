# coding: utf-8

import ssl
import errno

OK = 0

IO_WOULD_BLOCK = [
    errno.EWOULDBLOCK,
    errno.EAGAIN,
    ssl.SSL_ERROR_WANT_READ,
    ssl.SSL_ERROR_WANT_WRITE
]

TRANSPORT_CLOSED = ConnectionError("transport closed")
TRANSPORT_ABORTED = ConnectionError("transport aborted")


class InvalidURL(Exception):

    pass


class InvalidHeader(Exception):

    pass


class BadStatusLine(Exception):

    pass


class TooManyRedirects(Exception):

    pass


class NotEnoughData(Exception):

    pass
