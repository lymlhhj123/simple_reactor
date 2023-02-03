# coding: utf-8

from libreactor import const


class Protocol(object):

    connection = None
    event_loop = None
    ctx = None

    def connection_made(self):
        """

        server side accept new connection
        :return:
        """
        self.ctx.connection_made(self)

    def connection_established(self):
        """

        client side connection established
        :return:
        """
        self.ctx.connection_established(self)

    def connection_error(self, error: const.ConnectionErr):
        """

        :param error:
        :return:
        """

    def send_data(self, data: bytes):
        """

        :param data:
        :return:
        """
        if not isinstance(data, bytes):
            return

        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
