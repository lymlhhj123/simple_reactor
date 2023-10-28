# coding: utf-8

from collections import deque


class UDP(object):

    def __init__(self, loop):

        self.loop = loop

        self._send_buf = deque()

    def send_dgram(self, dgram, addr=None):

        self._send_buf.append((dgram, addr))


class UDPServer(UDP):

    pass


class UDPClient(UDP):

    pass
