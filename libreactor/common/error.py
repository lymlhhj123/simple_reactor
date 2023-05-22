# coding: utf-8

import os
from errno import *

OK = 0
SELF_CONNECT = 65536
USER_CLOSED = 65537
USER_ABORT = 65538
PEER_CLOSED = 65539


error_map = {
    SELF_CONNECT: "tcp self connect",
    USER_CLOSED: "connection closed by user",
    USER_ABORT: "connection abort by user",
    PEER_CLOSED: "connection closed by peer",
}


class Reason(object):

    def __init__(self, err_code):
        """

        :param err_code:
        """
        self.err_code = err_code

    def what(self):
        """

        :return:
        """
        readable = error_map.get(self.err_code)
        if not readable:
            readable = os.strerror(self.err_code)

        return readable


def is_bad_error(err_code):
    """

    :param err_code:
    :return:
    """
    return err_code not in [OK, EWOULDBLOCK, EAGAIN]
