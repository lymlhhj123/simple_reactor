# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import UdpClient
from libreactor.protocol import Protocol


class MyProtocol(Protocol):

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
ctx.set_established_callback(on_established)

ev = EventLoop()

client = UdpClient("127.0.0.1", 9527, ctx, ev)
client.start()

ev.loop()
