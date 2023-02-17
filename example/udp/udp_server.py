# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import UdpV6Server
from libreactor.protocol import Protocol


class MyProtocol(Protocol):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        print(f"{data}")


class MyContext(Context):

    protocol_cls = MyProtocol


ctx = MyContext()
ev = EventLoop()

server = UdpV6Server(9527, ctx, ev)
server.start()

ev.loop()
