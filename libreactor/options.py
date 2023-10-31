# coding: utf-8


class Options(object):

    def __init__(self):

        self.connect_timeout = 10
        self.tcp_no_delay = False
        self.tcp_keepalive = False
        self.reuse_addr = True
        self.close_on_exec = False
        self.ipv6_only = False
        self.backlog = 128
        self.ssl_options = None


class SSLOptions(object):

    def __init__(self):

        self.server_hostname = None
