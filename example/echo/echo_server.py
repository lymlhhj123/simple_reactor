# coding: utf-8

from libreactor import Context
from libreactor import EventLoop
from libreactor import TcpServer
from libreactor.protocol import TcpProtocol


class MyProtocol(TcpProtocol):

    def data_received(self, data: bytes):
        """

        :param data:
        :return:
        """
        self.connection.write(data)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
