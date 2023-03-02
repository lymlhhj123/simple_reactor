# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import UdpServer
from libreactor.protocol import Protocol


class MyProtocol(Protocol):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        print(f"{data}")


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ctx = MyContext()
ev = EventLoop()

server = UdpServer(9527, ctx, ev)

ev.loop()
