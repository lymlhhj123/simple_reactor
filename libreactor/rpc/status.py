# coding: utf-8

import enum


class Status(enum.IntEnum):
    """
    socket read/write status, both tcp/unix/udp
    """

    OK = 0
    CLOSED = 1
    BROKEN_PIPE = 2
    LOST = 3
