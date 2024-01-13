# coding: utf-8


class Options(object):

    def __init__(self):

        self.dns_resolve_timeout = 10
        self.connect_timeout = 10
        self.tcp_no_delay = True
        self.tcp_keepalive = True
        self.reuse_addr = True
        self.close_on_exec = True
        self.backlog = 128
        self.allow_broadcast = False


class SSLOptions(object):

    def __init__(self):

        self.server_hostname = None
        self.cert_file = None
        self.key_file = None
