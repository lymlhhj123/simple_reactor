# coding: utf-8

from libreactor import ClientContext
from libreactor import EventLoop
from libreactor import TcpClient
from libreactor import Options
from libreactor import LineReceiver

line_format = "this is line {}"


class MyProtocol(LineReceiver):

    def __init__(self):

        super(MyProtocol, self).__init__()

        self.line_no = 2

    def line_received(self, line: str):
        """

        :param line:
        :return:
        """
        line_no, self.line_no = self.line_no, self.line_no + 1
        self.event_loop.call_later(2, self.send_line, line_format.format(line_no))


class MyContext(ClientContext):

    protocol_cls = MyProtocol

    def connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        protocol.send_line(line_format.format(1))


ev = EventLoop()

client = TcpClient("127.0.0.1", 9527, ev, MyContext(), Options())
client.connect()

ev.loop()
