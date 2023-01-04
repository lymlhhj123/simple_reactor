# coding: utf-8

import enum


class State(enum.IntEnum):
    """
    stream tcp/unix connection state
    """

    CONNECTED = 0
    CONNECTING = 1
    DISCONNECTING = 2
    DISCONNECTED = 3


class ConnectType(enum.IntEnum):

    TCP = 0
    UNIX = 1
