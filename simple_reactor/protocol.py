# coding: utf-8


class BaseProtocol(object):

    loop = None
    transport = None
    factory = None

    def make_connection(self, loop, transport, factory):
        """auto called when make new connection"""
        self.loop = loop
        self.transport = transport
        self.factory = factory

    def connection_lost(self, exc):
        """auto called when connection lost"""

    def close(self):
        """close protocol"""


class StreamProtocol(BaseProtocol):

    def connection_made(self):
        """called when server side accept new connection"""

    def connection_established(self):
        """called when client side connection established"""

    def data_received(self, data: bytes):
        """called when data received by transport"""

    def eof_received(self):
        """called when peer close write side"""

    def pause_write(self):
        """called when transport write buffer >= high water"""

    def resume_write(self):
        """called when transport write buffer <= low water"""


class DatagramProtocol(BaseProtocol):

    def connection_prepared(self):
        """called when transport is prepare to work"""

    def datagram_received(self, datagram, addr):
        """called when data received from socket"""

    def connection_error(self, exc):
        """called when error happened on write/read"""
