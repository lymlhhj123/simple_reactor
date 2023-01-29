# coding: utf-8

from .. import const


class TcpProtocol(object):

    def __init__(self):

        self.ctx = None
        self.connection = None
        self.event_loop = None

    def set_args(self, ctx, conn, ev):
        """

        don't call this function directly, auto called by framework
        :param ctx:
        :param conn:
        :param ev:
        :return:
        """
        self.ctx = ctx
        self.connection = conn
        self.event_loop = ev

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

    # def send_dgram(self, data, addr):
    #     """
    #     dgram protocol
    #     :param data:
    #     :param addr:
    #     :return:
    #     """
    #     self.connection.write_dgram(data, addr)
    #
    # def dgram_received(self, data, addr):
    #     """
    #     dgram protocol
    #     :param data:
    #     :param addr:
    #     :return:
    #     """

    def close_connection(self):
        """

        :return:
        """
        self.connection.close()
