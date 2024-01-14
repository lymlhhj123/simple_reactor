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
