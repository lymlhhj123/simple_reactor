# coding: utf-8

from libreactor import Context
from libreactor import EventLoop
from libreactor import TcpServer
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

server = TcpServer(9527, ev, MyContext())
server.start()

ev.loop()
