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

    STR_ERROR: dict = {
        OK: "OK",
        TIMEOUT: "Timeout",
        CLOSED: "Connection closed",
        DNS_RESOLVE_FAILED: "Failed to resolve dns",
        DO_AGAIN: "Resource temporarily unavailable"
    }

    @classmethod
    def is_error(cls, err_code):
        """

        :param err_code:
        :return:
        """
        return err_code not in {cls.OK, cls.DO_AGAIN}

    @classmethod
    def str_error(cls, err_code):
        """

        :param err_code:
        :return:
        """
        reason = os.strerror(err_code)
        if not reason:
            reason = cls.STR_ERROR.get(err_code, "Unknown error")

        return reason


class IPAny(object):

    V4 = "0.0.0.0"
    V6 = "::"
