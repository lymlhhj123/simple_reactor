# coding: utf-8

import json

from libreactor.context import Context
from libreactor.protocol import MsgProtocol


def succeed_callback(protocol):
    """

    :param protocol:
    :return:
    """
    msg = {
        "a": 1,
        "b": 2,
        "c": 3,

    }
    protocol.send_msg(json.dumps(msg))


def tcp_main(ctx):
    """

    :return:
    """
    ctx.connect_tcp("127.0.0.1", 9527, on_connection_established=succeed_callback)

    ctx.main_loop()


context = Context(stream_protocol_cls=MsgProtocol, log_debug=True)

tcp_main(context)
