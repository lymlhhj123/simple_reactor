# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpV4Server
from libreactor.protocol import Protocol


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.connection.write(data)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpV4Server(9527, ev, MyContext())
server.start()

ev.loop()
