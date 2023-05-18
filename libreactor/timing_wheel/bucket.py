# coding: utf-8

from threading import Lock

from ..common import linked_list


class Bucket(object):

    def __init__(self):

        self.lock = Lock()
        self.list = linked_list.LinkedList()

        self.expiration = -1

    def add_timer(self, timer):
        """

        :param timer:
        :return:
        """
        node = linked_list.Node(timer)
        with self.lock:
            self.list.add_node(node)

            timer.bucket = self
            timer.node = node

    def remove_timer(self, timer):
        """

        :param timer:
        :return:
        """
        with self.lock:
            self._remove_timer(timer)

    def _remove_timer(self, timer):
        """

        :param timer:
        :return: 
        """
        if timer.bucket != self:
            return False

        self.list.remove_node(timer.node)
        timer.bucket = None
        timer.node = None
        return True

    def flush(self, callback):
        """

        :param callback:
        :return:
        """
        timer_list = []
        with self.lock:
            while not self.list.empty():
                node = self.list.front()
                timer = node.v
                self._remove_timer(timer)
                if timer.is_cancelled():
                    continue

                timer_list.append(timer)

            self.expiration = -1

        for t in timer_list:
            callback(t)

    def set_expiration(self, expiration):
        """

        :param expiration:
        :return:
        """
        with self.lock:
            self.expiration, old_expiration = expiration, self.expiration
            return old_expiration != expiration
