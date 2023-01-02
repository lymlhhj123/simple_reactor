# coding: utf-8


class Protocol(object):

    def __init__(self):

        self.context = None
        self.connection = None
        self.event_loop = None

    def connection_made(self, connection, event_loop, ctx):
        """

        server side accept new connection
        :param connection:
        :param event_loop:
        :param ctx:
        :return:
        """
        self.connection = connection
        self.event_loop = event_loop
        self.context = ctx

    def connection_established(self, connection, event_loop, ctx):
        """

        client side connection established
        :param connection:
        :param event_loop:
        :param ctx:
        :return:
        """
        self.connection = connection
        self.event_loop = event_loop
        self.context = ctx

    def connection_lost(self):
        """

        :return:
        """

    def connection_done(self):
        """

        :return:
        """

    def safe_send_data(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.event_loop.call_soon(self.send_data, data)

    def send_data(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.connection.write(data)

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """

    def safe_close_connection(self):
        """

        :return:
        """
        self.event_loop.call_soon(self.close_connection)

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
