# coding: utf-8

from libreactor import ClientContext
from libreactor import EventLoop
from libreactor import TcpClient
from libreactor import Options
from libreactor import MessageReceiver
from libreactor import common

logger = common.get_logger()
common.logger_init(logger)


class MyProtocol(MessageReceiver):

    def __init__(self):

        super(MyProtocol, self).__init__()

        self.idx = 0

    def msg_received(self, msg):
        """

        :param msg:
        :return:
        """
        logger.info(f"msg received: {msg.json()}")

        idx, self.idx = self.idx, self.idx + 1
        data = {idx: idx}
        self.send_json(data)


class MyContext(ClientContext):

    protocol_cls = MyProtocol

    def connection_established(self, protocol):
        """

        :param protocol:
        :return:
        """
        data = {-1: -1}
        protocol.send_json(data)


ev = EventLoop.current()

client = TcpClient("::1", 9527, ev, MyContext(), Options())
client.connect()

ev.loop()
