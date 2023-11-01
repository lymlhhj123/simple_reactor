# coding: utf-8


class Options(object):

    def __init__(self):

        self.connect_timeout = 10
        self.tcp_no_delay = False
        self.tcp_keepalive = False
        self.reuse_addr = True
        self.close_on_exec = False
        self.backlog = 128


class SSLOptions(object):

    def __init__(self):

        self.server_hostname = None
        self.cert_file = None
        self.key_file = None
