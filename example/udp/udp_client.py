# coding: utf-8

from libreactor import UdpProtocol
from libreactor import Context
from libreactor import UdpClient
from libreactor import EventLoop


class MyProtocol(UdpProtocol):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """

    def write_dgram(self):
        """

        :return:
        """
        self.event_loop.call_every(1, self.connection.write, b"data")


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.write_dgram()


class MyContext(Context):

    protocol_cls = MyProtocol


ctx = MyContext()
ctx.set_callback(on_established)

ev = EventLoop()

client = UdpClient("127.0.0.1", 9527, ctx, ev)
client.start()

ev.loop()
