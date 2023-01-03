# coding: utf-8

from libreactor.context import Context
from libreactor.protocol import Protocol


class DgramProtocol(Protocol):

    def dgram_received(self, data, addr):
        """

        :param data:
        :param addr:
        :return:
        """
        self.context.logger().info(f"{data}, {addr}")

        self.send_dgram(b"OK", addr)


def udp_main(ctx):
    """

    :param ctx:
    :return:
    """
    ctx.listen_udp(9528)


context = Context()
udp_main(context)
context.main_loop()
