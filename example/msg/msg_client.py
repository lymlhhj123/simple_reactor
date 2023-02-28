# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpV6Client
from libreactor.basic_protocols import MessageReceiver


class MyProtocol(MessageReceiver):

    def __init__(self):

        super(MyProtocol, self).__init__()

        self.idx = 0

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        print(f"{msg.json()}")

        idx, self.idx = self.idx, self.idx + 1
        data = {idx: idx}
        self.send_json(data)


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    data = {-1: -1}
    protocol.send_json(data)


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)

client = TcpV6Client("::1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
