# coding: utf-8

import heapq

from .timer import Timer


class TimerQueue(object):

    def __init__(self):

        self.queue = []
        self.cancelled = 0

    def put(self, timer):
        """

        :param timer:
        :return:
        """
        heapq.heappush(self.queue, timer)

    def cancel(self, timer):
        """

        :param timer:
        :return:
        """
        assert isinstance(timer, Timer)
        self.cancelled += 1

    def first(self):
        """

        :return:
        """
        return self.queue[0] if self.queue else None

    def resize(self):
        """

        :return:
        """
        if self.cancelled < 100:
            return

        queue = [t for t in self.queue if t.is_cancelled() is False]
        heapq.heapify(queue)
        self.queue = queue
        self.cancelled = 0

    def retrieve(self, deadline):
        """

        :param deadline:
        :return:
        """
        timer_list = []
        queue = self.queue
        while queue:
            if queue[0].when > deadline:
                break

            timer = heapq.heappop(queue)
            if timer.is_cancelled():
                self.cancelled -= 1
                continue

            timer_list.append(timer)

        self.queue = queue
        return timer_list
