# coding: utf-8

from libreactor import Context
from libreactor import EventLoop
from libreactor import TcpClient
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


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.send_line(line_format.format(1))


ev = EventLoop()

ctx = MyContext()
ctx.set_on_established(on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
