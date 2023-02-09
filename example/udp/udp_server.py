# coding: utf-8

from libreactor import Context
from libreactor import UdpServer
from libreactor import EventLoop
from libreactor.protocol import UdpProtocol


class MyProtocol(UdpProtocol):

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

server = UdpServer(9527, ctx, ev)
server.start()

ev.loop()
