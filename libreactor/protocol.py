# coding: utf-8


class BaseProtocol(object):

    loop = None
    transport = None

    def make_connection(self, loop, transport):
        """auto called when make new connection"""
        self.loop = loop
        self.transport = transport

    def connection_lost(self, reason):
        """auto called when connection lost

        :return:
        """


class Protocol(BaseProtocol):

    def connection_made(self):
        """
        auto called when server side accept new connection
        :return:
        """

    def connection_established(self):
        """
        auto called when client side connection established
        :return:
        """

    def data_received(self, data: bytes):
        """auto called when data received by transport

        :param data:
        :return:
        """

    def pause_write(self):
        """auto called when transport write buffer >= high water"""

    def resume_write(self):
        """auto called when transport write buffer <= low water"""


class ProcessProtocol(BaseProtocol):

    def data_received(self, fd, data):
        """auto called when stdout/stdout data received"""

    def connection_lost(self, reason):

        self.process_end(reason)

    def process_end(self, reason):
        """auto called when child process exit"""


class DatagramProtocol(object):

    def dgram_received(self, dgram):
        """called when data received from socket"""

    def connection_error(self, reason):
        """called when error happened in write"""
