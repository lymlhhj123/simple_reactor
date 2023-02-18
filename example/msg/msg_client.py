# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpV6Client
from libreactor.basic_protocols import MessageReceiver


class MyProtocol(MessageReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        print(f"{msg.json()}")
        self.event_loop.call_later(5, self.send_msg, msg)


class MyContext(Context):

    protocol_cls = MyProtocol


def on_established(protocol):
    """

    :param protocol:
    :return:
    """
    user_data = {"1": "2", "3": "4"}
    protocol.send_json(user_data)


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)

client = TcpV6Client("::1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
