# coding: utf-8


class Protocol(object):

    event_loop = None
    ctx = None
    transport = None

    def make_connection(self, ev, ctx, transport):
        """auto called when client/server side make new connection"""
        self.event_loop = ev
        self.ctx = ctx
        self.transport = transport

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

    def connection_lost(self, reason):
        """
        auto called when connection lost
        :return:
        """

    def data_received(self, data: bytes):
        """auto called when data received by transport

        :param data:
        :return:
        """

    def data_sent(self, size):
        """auto called when data has been sent by transport

        :param size:
        :return:
        """
