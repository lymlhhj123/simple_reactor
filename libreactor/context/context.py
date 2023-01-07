# coding: utf-8

from libreactor import logger

from ..protocol import Protocol
from ..protocol import MessageReceiver


class Context(object):

    stream_protocol_cls = MessageReceiver
    dgram_protocol_cls = Protocol

    def __init__(self):

        self._logger = logger.get_logger(False)

        self._conn_id = 0
        self._connection_map = {}

    def logger(self):
        """

        :return:
        """
        return self._logger

    def add_connection(self, connection):
        """

        :param connection:
        :return:
        """
        conn_id = self._conn_id
        self._connection_map[conn_id] = connection
        self._conn_id += 1
        return conn_id

    def remove_connection(self, conn_id):
        """

        :param conn_id:
        :return:
        """
        self._connection_map.pop(conn_id, None)

    def build_stream_protocol(self):
        """

        :return:
        """
        return self.stream_protocol_cls()

    def build_dgram_protocol(self):
        """

        :return:
        """
        return self.dgram_protocol_cls()

    def on_connection_done(self):
        """
        called when connection closed by peer
        :return:
        """

    def on_connection_lost(self, error_code):
        """
        called when connection lost
        :param error_code:
        :return:
        """

    def on_connection_close(self):
        """
        called when connection closed
        :return:
        """

    # def listen_udp(self, port, event_loop):
    #     """
    #
    #     :param port:
    #     :return:
    #     """
    #     server = rpc.UdpServer(port, self)
    #     server.start()
    #
    # def connect_udp(self, endpoint, event_loop):
    #     """
    #
    #     :param endpoint:
    #     :return:
    #     """
    #     client = rpc.UdpClient(endpoint, self)
    #     client.start()
