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


class ErrorCode(object):

    OK = 0
    TIMEOUT = 65536
    CLOSED = 65537
    DNS_RESOLVE_FAILED = 65538
    DO_AGAIN = 65539

    MAP = {
        OK: "OK",
        TIMEOUT: "Timeout",
        CLOSED: "Connection closed by peer",
        DNS_RESOLVE_FAILED: "Failed to resolve dns",
        DO_AGAIN: "Resource temporarily unavailable"
    }

    @staticmethod
    def is_error(err_code):
        """

        :param err_code:
        :return:
        """
        return not (err_code == ErrorCode.OK or
                    err_code == ErrorCode.DO_AGAIN)

    @staticmethod
    def str_error(err_code):
        """

        :param err_code:
        :return:
        """
        reason = os.strerror(err_code)
        if not reason:
            reason = ErrorCode.MAP.get(err_code, "Unknown error")

        return reason


class IPAny(object):

    V4 = "0.0.0.0"
    V6 = "::"
