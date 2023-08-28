# coding: utf-8

from .protocol import Protocol


class _BaseContext(object):

    protocol_cls = Protocol

    def build_protocol(self):
        """

        :return:
        """
        return self.protocol_cls()


class ClientContext(_BaseContext):

    def connection_failed(self, connector, reason):
        """auto called when client failed to established connection

        :param connector:
        :param reason:
        :return:
        """

    def connection_lost(self, connector, reason):
        """auto called when client connection lost

        :param connector:
        :param reason:
        :return:
        """

    def connection_established(self, protocol):
        """auto called when client connection established

        :param protocol:
        :return:
        """


class ServerContext(_BaseContext):

    def connection_made(self, protocol):
        """auto called when server side connection made

        :param protocol:
        :return:
        """
