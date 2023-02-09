# coding: utf-8

from libreactor import Context
from libreactor import EventLoop
from libreactor import TcpServer
from libreactor.basic_protocols import LineReceiver


class MyProtocol(LineReceiver):

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
        print(f"{line}")
        self.send_line(line)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
