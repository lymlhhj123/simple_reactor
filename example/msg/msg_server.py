# coding: utf-8

from libreactor.context import Context
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpV6Server
from libreactor.basic_protocols import MessageReceiver


class MyProtocol(MessageReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.send_msg(msg)


class MyContext(Context):

    protocol_cls = MyProtocol


ev = EventLoop()

server = TcpV6Server(9527, ev, MyContext())
server.start()

ev.loop()
