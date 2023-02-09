# coding: utf-8

from libreactor import const


class Protocol(object):

    connection = None
    event_loop = None
    ctx = None

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

    def connection_error(self, error: const.ConnectionErr):
        """
        auto called when connection error happened
        :param error:
        :return:
        """

    def connection_closed(self):
        """
        auto called when connection closed
        :return:
        """

    def data_received(self, data: bytes):
        """
        used by tcp
        :param data:
        :return:
        """

    def dgram_received(self, data, addr):
        """
        used by udp
        :param data:
        :param addr:
        :return:
        """

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
