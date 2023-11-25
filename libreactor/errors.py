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
