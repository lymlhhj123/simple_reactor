# coding: utf-8

from libreactor import DgramReceiver
from libreactor import Context
from libreactor import UdpClient
from libreactor import EventLoop


class MyProtocol(DgramReceiver):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        self.event_loop.call_later(1, self.connection.write, data)

    def write_dgram(self):
        """

        :return:
        """
        self.connection.write(b"this is dgram")


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.write_dgram()


class MyContext(Context):

    protocol_cls = MyProtocol


ctx = MyContext(on_established=on_established)
ev = EventLoop()

client = UdpClient("127.0.0.1", 9527, ctx, ev)
client.start()
