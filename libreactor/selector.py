# coding: utf-8

import select


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
        if event & select.POLLIN:
            self.r_list.add(fd)

        if event & select.POLLOUT:
            self.w_list.add(fd)

    def unregister(self, fd):
        """

        :param fd:
        :return:
        """
        self.r_list.discard(fd)
        self.w_list.discard(fd)

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
            ev_map[fd] = select.POLLIN

        for fd in w:
            ev = ev_map.get(fd, 0)
            ev_map[fd] = ev | select.POLLOUT

        for fd in x:
            ev = ev_map.get(fd, 0)
            ev |= select.POLLOUT
            ev |= select.POLLIN
            ev_map[fd] = ev

        return ev_map.items()
