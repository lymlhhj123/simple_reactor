# coding: utf-8

import enum


class ConnectionState(enum.IntEnum):
    """
    stream tcp/unix connection state
    """

    CONNECTED = 0
    CONNECTING = 1
    DISCONNECTING = 2
    DISCONNECTED = 3


class RWState(enum.IntEnum):
    """
    socket read/write status
    """

    OK = 0
    CLOSED = 1
    BROKEN_PIPE = 2
    LOST = 3
    ERROR = 4
