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
        used by tcp
        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        if not isinstance(data, bytes):
            return

        self.connection.write(data)

    def data_received(self, data: bytes):
        """
        used by tcp
        :param data:
        :return:
        """

    def send_dgram(self, data, addr):
        """
        used by udp
        :param data:
        :param addr:
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
