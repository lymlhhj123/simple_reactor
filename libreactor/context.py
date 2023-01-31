# coding: utf-8

from libreactor import StreamReceiver


class Context(object):

    protocol_cls = StreamReceiver

    def __init__(self, on_established=None, on_made=None):
        """

        :param on_established:
        :param on_made:
        """
        self.on_established = on_established
        self.on_made = on_made

    def connection_established(self, protocol):
        """

        auto called when client connection established
        :param protocol:
        :return:
        """
        if self.on_established:
            self.on_established(protocol)

    def connection_made(self, protocol):
        """

        auto called when server side connection made
        :param protocol:
        :return:
        """
        if self.on_made:
            self.on_made(protocol)

    def build_protocol(self):
        """

        :return:
        """
        return self.protocol_cls()
