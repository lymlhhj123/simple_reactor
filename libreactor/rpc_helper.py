# coding: utf-8

import socket

from .coroutine import coroutine
from . import sock_helper
from . import fd_helper
from . import error
from .connector import Connector
from .acceptor import Acceptor
from .options import Options
from .factory import Factory


@coroutine
def connect_tcp(loop, host, port, proto_factory, *, factory=Factory(), options=Options(), ssl_options=None):
    """create tcp client"""
    addr_list = yield loop.ensure_resolved(host, port)

    protocol = None
    ex = None
    for res in addr_list:
        family, _, _, _, sa = res
        connector = Connector(loop, family, sa, proto_factory, factory, options, ssl_options)
        try:
            protocol = yield connector.connect()
            break
        except error.Failure as e:
            ex = e
            continue

    if not protocol:
        raise ex

    return protocol


@coroutine
def listen_tcp(loop, port, proto_factory, *, host=None, factory=Factory(), options=Options(), ssl_options=None):
    """create tcp server"""

    socks = yield _bind_tcp_socket(loop, port, host, options)

    acceptor = Acceptor(loop, socks, proto_factory, factory, options, ssl_options)
    acceptor.start()
    return acceptor


@coroutine
def _bind_tcp_socket(loop, port, host=None, options=Options()):
    """create socket and bind to (host, port)"""
    addr_list = yield loop.ensure_resolved(host, port)

    socks = []
    for res in addr_list:
        af, sock_type, proto, _, sa = res

        sock = socket.socket(af, sock_type, proto)

        if af == socket.AF_INET6:
            # ipv6 socket only accept ipv6 address
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

        sock_helper.set_sock_async(sock)

        if options.reuse_addr:
            sock_helper.set_reuse_addr(sock)

        fd_helper.close_on_exec(sock.fileno(), options.close_on_exec)

        sock.bind(sa)
        sock.listen(options.backlog)
        socks.append(sock)

    return socks
