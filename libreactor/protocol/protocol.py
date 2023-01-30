# coding: utf-8

from libreactor import const


class Protocol(object):

    def __init__(self):

        self.connection = None
        self.event_loop = None
        self.ctx = None

    def connection_made(self, conn, ev, ctx):
        """

        server side accept new connection
        :param conn:
        :param ev:
        :param ctx:
        :return:
        """
        self._set_args(conn, ev, ctx)
        self.ctx.connection_made(self)

    def connection_established(self, conn, ev, ctx):
        """

        client side connection established
        :param conn:
        :param ev:
        :param ctx:
        :return:
        """
        self._set_args(conn, ev, ctx)
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

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
