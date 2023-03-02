# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpServer
from libreactor.basic_protocols import LineReceiver


class MyProtocol(LineReceiver):

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
        print(f"{line}")
        self.send_line(line)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())

ev.loop()
