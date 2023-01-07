# coding: utf-8

import select


class EPoller(object):

    def __init__(self):

        self._poller = select.epoll()

    def register(self, fd, event):
        """

        :param fd:
        :param event:
        :return:
        """
        self._poller.register(fd, event)

    def modify(self, fd, event):
        """

        :param fd:
        :param event:
        :return:
        """
        self._poller.modify(fd, event)

    def unregister(self, fd):
        """

        :param fd:
        :return:
        """
        self._poller.unregister(fd)

    def poll(self, timeout):
        """

        :param timeout:
        :return:
        """
        return self._poller.poll(timeout)
