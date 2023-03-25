# coding: utf-8


class Options(object):

    def __init__(self):

        self._connect_timeout = 10
        self._tcp_no_delay = False
        self._tcp_keepalive = False
        self._reuse_addr = True
        self._close_on_exec = False
        self._ipv6_only = False
        self._backlog = 128

    @property
    def connect_timeout(self):

        return self._connect_timeout

    @connect_timeout.setter
    def connect_timeout(self, timeout):

        self._connect_timeout = timeout

    @property
    def tcp_no_delay(self):

        return self._tcp_no_delay

    @tcp_no_delay.setter
    def tcp_no_delay(self, flag):

        self._tcp_no_delay = flag

    @property
    def tcp_keepalive(self):

        return self._tcp_keepalive

    @tcp_keepalive.setter
    def tcp_keepalive(self, flag):

        self._tcp_keepalive = flag

    @property
    def reuse_addr(self):

        return self._reuse_addr

    @reuse_addr.setter
    def reuse_addr(self, flag):

        self._reuse_addr = flag

    @property
    def close_on_exec(self):

        return self._close_on_exec

    @close_on_exec.setter
    def close_on_exec(self, flag):

        self._close_on_exec = flag

    @property
    def ipv6_only(self):

        return self._ipv6_only

    @ipv6_only.setter
    def ipv6_only(self, flag):

        self._ipv6_only = flag

    @property
    def backlog(self):

        return self._backlog

    @backlog.setter
    def backlog(self, backlog):

        self._backlog = backlog
