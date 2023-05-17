# coding: utf-8

from threading import Lock

from ..common import utils
from .timer import Timer
from .timing_wheel import TimingWheel


class TimerScheduler(object):

    def __init__(self, ev, tick_ms=100, wheel_size=20):
        """

        :param ev:
        :param tick_ms:
        :param wheel_size:
        """
        self.ev = ev
        self.timing_wheel = TimingWheel(tick_ms, wheel_size)

        self.lock = Lock()

    def call_later(self, delay, func, *args, **kwargs):
        """

        :param delay: second
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        deadline = utils.monotonic_ms() + delay * 1000
        return self.call_at(deadline, func, *args, **kwargs)

    def call_at(self, when, func, *args, **kwargs):
        """

        :param when: second
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        t = Timer(when * 1000, func, *args, **kwargs)
        self._add_timer(t)
        return t

    def _add_timer(self, t):
        """

        :param t:
        :return:
        """
        with self.lock:
            bucket, expiration_updated = self.timing_wheel.add(t)
            if not bucket:  # timer already timeout, run it
                self.ev.call_soon(t.run)
            elif bucket and expiration_updated:
                # ms to sec
                self.ev.call_at(bucket.expiration // 1000, self._bucket_expiration, bucket)

    def _bucket_expiration(self, bucket):
        """

        :param bucket:
        :return:
        """
        self.timing_wheel.advance_clock(bucket.expiration)
        bucket.flush(self._add_timer)
