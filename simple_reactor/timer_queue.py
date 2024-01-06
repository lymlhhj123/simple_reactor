# coding: utf-8

import heapq

from .timer import TimerHandle


class TimerQueue(object):

    def __init__(self):

        self.queue = []
        self.cancelled_count = 0

    def put(self, timer):
        """

        :param timer:
        :return:
        """
        heapq.heappush(self.queue, timer)

    def cancel(self, handle):
        """

        :param handle:
        :return:
        """
        assert isinstance(handle, TimerHandle)
        self.cancelled_count += 1

    def first(self):
        """

        :return:
        """
        return self.queue[0] if self.queue else None

    def resize(self):
        """

        :return:
        """
        if self.cancelled_count < 100:
            queue = self.queue
            while queue and queue[0].cancelled():
                heapq.heappop(queue)
                self.cancelled_count -= 1
            return

        queue = [t for t in self.queue if t.cancelled() is False]
        heapq.heapify(queue)
        self.queue = queue
        self.cancelled_count = 0

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
            if timer.cancelled():
                self.cancelled_count -= 1
                continue

            timer_list.append(timer)

        self.queue = queue
        return timer_list
