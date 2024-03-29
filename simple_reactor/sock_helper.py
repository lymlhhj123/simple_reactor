# coding: utf-8

import socket


def set_sock_async(sock: socket.socket):
    """set sock non-blocking"""
    sock.setblocking(False)


def set_reuse_addr(sock: socket.socket):
    """set sock reuse addr"""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def set_ipv6_only(sock: socket.socket):
    """set socket only accept ipv6 sock"""
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)


def set_tcp_no_delay(sock: socket.socket):
    """set tcp no delay"""
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


def set_tcp_keepalive(sock: socket.socket, after_idle_sec=1, interval_sec=3, max_fails=5):
    """Set TCP keepalive on an open socket.

    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 3 failed ping (max_fails), or 15 seconds
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


def get_sock_error(sock: socket.socket):
    """get sock errno"""
    return sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)


def get_remote_addr(sock: socket.socket):
    """get remote addr"""
    return sock.getpeername()


def is_self_connect(sock: socket.socket):
    """return True if sock is self connect"""
    return sock.getsockname() == sock.getpeername()


def is_tcp_sock(sock: socket.socket):
    """return True if sock is tcp sock"""
    return sock.family in [socket.AF_INET, socket.AF_INET6] and sock.type == socket.SOCK_STREAM


def is_unix_sock(sock: socket):
    """return True if sock is unix sock"""
    return sock.family == socket.AF_UNIX


def close_sock(sock):
    """close socket"""
    try:
        sock.close()
    except (socket.error, Exception):
        pass
