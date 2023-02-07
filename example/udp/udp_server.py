# coding: utf-8

from libreactor import DgramReceiver
from libreactor import Context
from libreactor import UdpServer
from libreactor import EventLoop


class MyProtocol(DgramReceiver):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        print(f"{data}")
        self.connection.write(data, addr)


class MyContext(Context):

    protocol_cls = MyProtocol


ctx = MyContext()
ev = EventLoop()

client = UdpServer(9527, ctx, ev)
client.start()

ev.loop()
