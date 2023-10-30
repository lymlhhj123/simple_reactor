# coding: utf-8

import os
from errno import *

OK = 0
ESELFCONNECTED = 1024
ECONNCLOSED = 1025
EEOF = 1026

error_map = {
    ESELFCONNECTED: "connection self connect",
    ECONNCLOSED: "connection closed",
    EEOF: "eof received",
}


def is_bad_error(err_code):
    """

    :param err_code:
    :return:
    """
    return err_code not in [OK, EWOULDBLOCK, EAGAIN]


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
