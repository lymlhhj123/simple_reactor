# coding: utf-8

from threading import Lock

from .protocol import Protocol
from . import logging

logger = logging.get_logger()


class _BaseContext(object):

    protocol_cls = Protocol

    def __init__(self):

        self.lock = Lock()

    def connection_error(self, conn):
        """auto called when connection error happened

        :return:
        """

    def connection_closed(self, conn):
        """

        :param conn:
        :return:
        """

    def build_protocol(self):
        """

        :return:
        """
        return self.protocol_cls()


class ClientContext(_BaseContext):
    
    def __init__(self):
        
        super(ClientContext, self).__init__()

        self.client = None

    def bind_client(self, client):
        """bind client to this context, only bind once

        """
        with self.lock:
            if self.client:
                raise RuntimeError("context only bind client once")

            self.client = client

    def connection_established(self, protocol):
        """auto called when client connection established

        :param protocol:
        :return:
        """

    def connection_failure(self, conn):
        """auto called when client failed to establish connection

        :param conn:
        :return:
        """


class ServerContext(_BaseContext):

    def __init__(self):
        
        super(ServerContext, self).__init__()

        self.server = None

    def bind_server(self, server):
        """bind server to this context, only bind once

        """
        with self.lock:
            if self.server:
                raise RuntimeError("context only bind server once")

            self.server = server

    def connection_made(self, protocol):
        """auto called when server side connection made

        :param protocol:
        :return:
        """
