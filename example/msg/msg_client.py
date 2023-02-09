# coding: utf-8

import json

from libreactor import Message
from libreactor import Context
from libreactor import MessageReceiver
from libreactor import EventLoop
from libreactor import TcpClient


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
    msg = Message.create(json.dumps(user_data))
    protocol.send_msg(msg)


ev = EventLoop()

ctx = MyContext()
ctx.set_on_established(on_established)

client = TcpClient("127.0.0.1", 9527, ev, ctx, auto_reconnect=True)
client.start()

ev.loop()
