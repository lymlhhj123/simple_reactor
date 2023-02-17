# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpV4Server
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

server = TcpV4Server(9527, ev, MyContext())
server.start()

ev.loop()
