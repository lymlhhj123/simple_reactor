# coding: utf-8

import socket

from .coroutine import coroutine
from . import sock_helper
from . import fd_helper
from .connector import Connector
from .acceptor import Acceptor
from .options import Options
from . import const


@coroutine
def connect_tcp(loop, host, port, proto_factory, options=Options()):
    """create tcp client"""
    family = sock_helper.get_family_by_ip(host)
    connector = Connector(loop, family, (host, port), proto_factory, options)
    protocol = yield connector.connect()
    return protocol


def listen_tcp(loop, port, proto_factory, options=Options()):
    """create tcp server"""
    for host in [const.IPV4_ANY, const.IPV6_ANY]:
        family = sock_helper.get_family_by_ip(host)
        if family == socket.AF_INET and options.ipv6_only:
            continue

        sock = socket.socket(family, socket.SOCK_STREAM)
        if options.ipv6_only:
            assert family == socket.AF_INET6
            sock_helper.set_ipv6_only(sock)

        sock_helper.set_sock_async(sock)

        if options.reuse_addr:
            sock_helper.set_reuse_addr(sock)

        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        sock.bind((host, port))
        sock.listen(options.backlog)

        acceptor = Acceptor(loop, sock, proto_factory, options)
        acceptor.start()
