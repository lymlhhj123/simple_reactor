# coding: utf-8

import os


class ConnectionState(object):
    """
    tcp connection state
    """

    CONNECTED = 0
    CONNECTING = 1
    DISCONNECTING = 2
    DISCONNECTED = 3


class Error(object):

    OK = 0
    TIMEOUT = 65536
    CLOSED = 65537
    DNS_RESOLVE_FAILED = 65538

    STR_ERROR: dict = {
        OK: "ok",
        TIMEOUT: "timeout",
        CLOSED: "connection closed",
        DNS_RESOLVE_FAILED: "failed to resolve dns",
    }

    @classmethod
    def str_error(cls, error_code):
        """

        :param error_code:
        :return:
        """
        reason = os.strerror(error_code)
        if not reason:
            reason = Error.STR_ERROR.get(error_code, "Unknown error")

        return reason


class IPAny(object):

    V4 = "0.0.0.0"
    V6 = "::"
