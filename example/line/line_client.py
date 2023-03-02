# coding: utf-8

from libreactor.context import ClientContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpClient
from libreactor.basic_protocols import LineReceiver

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


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.send_line(line_format.format(1))


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx)

ev.loop()
