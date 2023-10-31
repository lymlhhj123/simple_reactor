# coding: utf-8

import os
import ssl
from errno import *

OK = 0
ESELFCONNECTED = 1024
ECONNCLOSED = 1025
EEOF = 1026
ESSL = 1027
EDNS = 1028

error_map = {
    ESELFCONNECTED: "connection self connect",
    ECONNCLOSED: "connection closed",
    EEOF: "eof received",
    ESSL: "ssl verify failed",
    EDNS: "dns resolved failed",
}

IO_WOULD_BLOCK = [EWOULDBLOCK, EAGAIN, ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE]


class Failure(Exception):

    def __init__(self, errcode):

        self._errcode = errcode

    def errno(self):

        return self._errcode

    def reason(self):
        """

        :return:
        """
        readable = error_map.get(self._errcode)
        if not readable:
            readable = os.strerror(self._errcode)

        return readable
