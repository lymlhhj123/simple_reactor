# coding: utf-8

from libreactor import Context
from libreactor import Protocol
from libreactor import EventLoop
from libreactor import TcpServer


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.send_data(data)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
