# coding: utf-8

from .context import Context
from .. import rpc


class ClientContext(Context):

    def __init__(self, auto_reconnect=False):

        super(ClientContext, self).__init__()
        self.auto_reconnect = auto_reconnect
        self.connector = None
        self.connection_established_cb = None

    def set_established_callback(self, callback):
        """

        :param callback:
        :return:
        """
        self.connection_established_cb = callback

    def connect_tcp(self, endpoint, event_loop, timeout=10):
        """

        :param endpoint: (ip ,port) pair
        :param event_loop:
        :param timeout:
        :return:
        """
        self.connector = rpc.TcpConnector(endpoint, self, event_loop)
        self.connector.start_connect(timeout)

    def on_connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        if self.connection_established_cb:
            self.connection_established_cb(protocol)

    def on_connection_failed(self, error_code):
        """
        called when establish connection failed

        :param error_code:
        :return:
        """

    def on_connection_timeout(self):
        """

        :return:
        """

    def on_connection_done(self):
        """

        :return:
        """

    def on_connection_lost(self, error_code):
        """

        :param error_code:
        :return:
        """

    def on_connection_close(self):
        """

        :return:
        """