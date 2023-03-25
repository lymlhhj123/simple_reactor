# coding: utf-8

from libreactor.context import ServerContext
from libreactor.event_loop import EventLoop
from libreactor.internet import TcpServer
from libreactor.options import Options
from libreactor.basic_protocols import MessageReceiver


class MyProtocol(MessageReceiver):

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        self.send_msg(msg)


class MyContext(ServerContext):

    protocol_cls = MyProtocol


ev = EventLoop.current()

server = TcpServer(9527, ev, MyContext(), Options())
server.start()

ev.loop()
