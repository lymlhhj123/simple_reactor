# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import Protocol


SERVER = ("127.0.0.1", 9528)


class DgramProtocol(Protocol):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        self.context.logger().info(f"{data}, {addr}")

        self.send_dgram(b"hello, world", SERVER)


def succeed_callback(protocol):
    """

    :param protocol:
    :return:
    """
    protocol.send_dgram(b"hello, world", SERVER)


def udp_main(ctx):
    """

    :param ctx:
    :return:
    """
    ctx.connect_udp("127.0.0.1", 9528, on_connection_established=succeed_callback)


context = Context(dgram_protocol_cls=DgramProtocol, log_debug=True)
udp_main(context)
context.main_loop()
