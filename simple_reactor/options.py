# coding: utf-8

from . import attrs


class Options(object):

    dns_resolve_timeout = attrs.Int(5)
    connect_timeout = attrs.Int(10)
    backlog = attrs.Int(128)
    tcp_no_delay = attrs.Bool()
    tcp_keepalive = attrs.Bool()
    reuse_addr = attrs.Bool()
    close_on_exec = attrs.Bool()
    allow_broadcast = attrs.Bool()


class SSLOptions(object):

    handshake_timeout = attrs.Int(10)
    ssl_client_ctx = attrs.SSLClientContext()
    ssl_server_ctx = attrs.SSLServerContext()
    server_hostname = attrs.String()
    cert_file = attrs.String()
    key_file = attrs.String()
