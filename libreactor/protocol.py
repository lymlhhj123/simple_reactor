# coding: utf-8


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

    def connection_error(self):
        """
        auto called when connection error happened
        :return:
        """

    def connection_closed(self):
        """
        auto called when connection closed
        :return:
        """

    def close_connection(self):
        """

        :return:
        """
        if self.connection:
            self.connection.close()
            del self.connection

    def data_received(self, data: bytes):
        """
        used by tcp
        :param data:
        :return:
        """

    def dgram_received(self, data: bytes, addr: tuple):
        """
        used by udp
        :param data:
        :param addr:
        :return:
        """
