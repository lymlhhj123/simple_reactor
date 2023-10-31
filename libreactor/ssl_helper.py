# coding: utf-8

import ssl


def ssl_client_context():
    """create client side ssl context"""
    context = ssl.create_default_context()
    return context


def ssl_server_context():
    """create server side ssl context"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    return context


def ssl_wrap_socket(ssl_context, sock, *, server_hostname=None, server_side=False):
    """wrap socket to ssl"""
    return ssl_context.wrap_socket(sock, server_hostname=server_hostname,
                                   server_side=server_side, do_handshake_on_connect=False)
