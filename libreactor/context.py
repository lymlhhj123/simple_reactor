# coding: utf-8

from libreactor import Protocol


class Context(object):

    protocol_cls = Protocol

    def __init__(self):

        self.on_established = None
        self.on_made = None

    def set_on_established(self, on_established):
        """

        :param on_established:
        :return:
        """
        self.on_established = on_established

    def set_on_made(self, on_made):
        """

        :param on_made:
        :return:
        """
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
