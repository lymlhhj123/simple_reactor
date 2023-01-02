# coding: utf-8

import threading
import functools
from datetime import datetime, timedelta


@functools.total_ordering
class Timer(object):

    def __init__(self, event_loop, callback, delay: int = None, fixed_time: str = None, repeated=False):
        """

        :param event_loop:
        :param callback:
        :param delay: int, 固定周期调用，比如每隔5秒
        :param fixed_time: str, 在固定的时间点调用，比如在每天的7点，"07:00:00"
        :param repeated:
        """
        self._callback = callback
        self._event_loop = event_loop
        
        self._delay = delay
        self._fixed_time = fixed_time
        self._repeated = repeated

        self._when = self._schedule()

        self._lock = threading.Lock()
        self._is_cancelled = False

    def is_repeated(self):
        """

        :return:
        """
        return self._repeated

    def schedule(self):
        """

        :return:
        """
        self._when = self._schedule()

    def _schedule(self):
        """

        :return:
        """
        if self._delay:
            interval = self._delay
        else:
            h, m, s = self._fixed_time.split(":")
            h = int(h) if h else 0
            m = int(m) if m else 0
            s = int(s) if s else 0

            now = datetime.now().replace(microsecond=0)
            expected_time = now.replace(hour=h, minute=m, second=s)
            if now > expected_time:
                expected_time = expected_time + timedelta(days=1)

            interval = max(0.0, (expected_time - now).total_seconds())

        return self._event_loop.time() + interval

    def run(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return

        self._callback.run()

    def cancel(self):
        """

        :return:
        """
        with self._lock:
            if self._is_cancelled:
                return

            self._is_cancelled = True

        self._event_loop.cancel_timer(self)

    def is_cancelled(self):
        """

        :return:
        """
        with self._lock:
            return self._is_cancelled

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        return (self._when, id(self)) == (other.when, id(other))

    def __gt__(self, other):
        """

        :param other:
        :return:
        """
        return (self._when, id(self)) > (other.when, id(other))

    @property
    def when(self):
        """

        :return:
        """
        return self._when
