# coding: utf-8


class Protocol(object):

    event_loop = None
    ctx = None

    def connection_made(self, conn):
        """
        auto called when server side accept new connection
        :return:
        """

    def connection_established(self, conn):
        """
        auto called when client side connection established
        :return:
        """

    def connection_lost(self, reason):
        """
        auto called when connection lost
        :return:
        """

    def data_received(self, data: bytes):
        """
        used by tcp
        :param data:
        :return:
        """

    def pause_write(self):
        """

        :return:
        """

    def resume_write(self):
        """

        :return:
        """
