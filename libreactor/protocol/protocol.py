# coding: utf-8


class Protocol(object):

    def __init__(self):

        self.context = None

        self.connection = None
        self.event_loop = None

    def set_connection_ev_ctx(self, connection, event_loop, ctx):
        """

        :param connection:
        :param event_loop:
        :param ctx:
        :return:
        """
        self.connection = connection
        self.event_loop = event_loop
        self.context = ctx

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
