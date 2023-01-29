# coding: utf-8


class ConnectionState(object):
    """
    tcp connection state
    """

    CONNECTED = 0
    CONNECTING = 1
    DISCONNECTING = 2
    DISCONNECTED = 3


class ConnectionErr(object):
    """
    tcp connection error
    """

    OK = 0
    TIMEOUT = 1
    CONNECT_FAILED = 2
    BROKEN_PIPE = 3
    PEER_CLOSED = 4
    USER_CLOSED = 5
    UNKNOWN = 6

    MAP = {
        TIMEOUT: "timeout",
        CONNECT_FAILED: "connect failed",
        BROKEN_PIPE: "broken pipe",
        PEER_CLOSED: "peer closed",
        USER_CLOSED: "user closed",
        UNKNOWN: "unknown",
    }
