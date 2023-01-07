# coding: utf-8


class Protocol(object):

    def __init__(self):

        self.ctx = None
        self.connection = None
        self.event_loop = None

    def set_ctx(self, ctx):
        """

        :param ctx:
        :return:
        """
        self.ctx = ctx

    def set_connection(self, connection):
        """

        :param connection:
        :return:
        """
        self.connection = connection

    def set_event_loop(self, event_loop):
        """

        :param event_loop:
        :return:
        """
        self.event_loop = event_loop

    def connection_made(self):
        """

        server side accept new connection
        :return:
        """

    def connection_established(self):
        """

        client side connection established
        :return:
        """

    def connection_lost(self):
        """

        :return:
        """

    def connection_done(self):
        """

        :return:
        """

    def send_data(self, data: bytes):
        """
        stream protocol
        :param data:
        :return:
        """
        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """

    def send_dgram(self, data, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """
        self.connection.write_dgram(data, addr)

    def dgram_received(self, data, addr):
        """
        dgram protocol
        :param data:
        :param addr:
        :return:
        """

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
