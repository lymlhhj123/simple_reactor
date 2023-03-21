# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpServer
from libreactor.protocol import Protocol


class MyProtocol(Protocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.connection.write(data)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
