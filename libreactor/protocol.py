# coding: utf-8

from libreactor import const


class Protocol(object):

    def __init__(self):

        self.connection = None
        self.event_loop = None
        self.ctx = None

    def connection_made(self):
        """

        server side accept new connection
        :return:
        """
        self.ctx.connection_made(self)

    def connection_established(self):
        """

        client side connection established
        :param conn:
        :param ev:
        :param ctx:
        :return:
        """
        self.ctx.connection_established(self)

    def _set_args(self, conn, ev, ctx):
        """

        :param conn:
        :param ev:
        :param ctx:
        :return:
        """
        self.connection = conn
        self.event_loop = ev
        self.ctx = ctx

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
