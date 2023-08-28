# coding: utf-8


class Protocol(object):

    event_loop = None
    ctx = None

    def connection_made(self, conn):
        """
        auto called when client/server side make new connection
        :return:
        """

    def connection_established(self, conn):
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
        """auto called when data received by socket

        :param data:
        :return:
        """

    def data_written(self, size):
        """auto called when data has been sent by socket

        :param size:
        :return:
        """
