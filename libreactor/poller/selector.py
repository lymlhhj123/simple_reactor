# coding: utf-8

import select

from . import _ev


class Selector(object):

    def __init__(self):

        self.r_list = set()
        self.w_list = set()

    def register(self, fd, event):
        """

        :param fd:
        :param event:
        :return:
        """
        if event & _ev.POLLIN:
            self.r_list.add(fd)

        if event & _ev.POLLOUT:
            self.w_list.add(fd)

    def unregister(self, fd):
        """

        :param fd:
        :return:
        """
        if fd in self.r_list:
            self.r_list.remove(fd)

        if fd in self.w_list:
            self.w_list.remove(fd)

    def modify(self, fd, event):
        """

        :param fd:
        :param event:
        :return:
        """
        self.unregister(fd)
        self.register(fd, event)

    def poll(self, timeout):
        """

        :param timeout:
        :return:
        """
        r, w, x = select.select(self.r_list, self.w_list, [], timeout)

        ev_map = {}

        for fd in r:
            ev_map[fd] = _ev.POLLIN

        for fd in w:
            ev = ev_map.get(fd, 0)
            ev_map[fd] = ev | _ev.POLLOUT

        for fd in x:
            ev = ev_map.get(fd, 0)
            ev |= _ev.POLLOUT
            ev |= _ev.POLLIN
            ev_map[fd] = ev

        return ev_map.items()
