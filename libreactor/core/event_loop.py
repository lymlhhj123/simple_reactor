# coding: utf-8

import errno
import select
import threading

from .. import poller
from .timer import Timer
from .timer_queue import TimerQueue
from .waker import Waker
from . import io_event
from .callback import Callback
from ..common import utils
from .future import Future

DEFAULT_TIMEOUT = 3.6  # sec

thread_local = threading.local()


class EventLoop(object):

    def __init__(self):

        self._time_func = utils.monotonic_time

        self._tid = threading.get_native_id()

        self._mutex = threading.Lock()
        self._callbacks = []
        self._timer_queue = TimerQueue()

        self._channel_map = {}
        self._poller = poller.Poller()

        self.waker = Waker(self)
        self.waker.enable_reading()

    @classmethod
    def current(cls):
        """

        :return:
        """
        ev = getattr(thread_local, "ev", None)
        if not ev:
            ev = cls()
            setattr(thread_local, "ev", ev)

        return ev

    def time(self):
        """

        thread safe
        :return:
        """
        return self._time_func()

    def call_soon(self, func, *args, **kwargs):
        """

        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        with self._mutex:
            self._callbacks.append(cb)

        self.wakeup()

    def call_later(self, delay, func, *args, **kwargs):
        """

        :param delay:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        return self.call_at(self.time() + delay, func, *args, **kwargs)

    def call_at(self, when, func, *args, **kwargs):
        """

        :param when:
        :param func:
        :param args:
        :param kwargs:
        :return:
        """
        cb = Callback(func, *args, **kwargs)
        return self._create_timer(cb, when)

    call_when = call_at

    def _create_timer(self, cb, when):
        """

        :param cb:
        :param when:
        :return:
        """
        t = Timer(self, cb, when)
        try:
            with self._mutex:
                self._timer_queue.put(t)

            return t
        finally:
            self.wakeup()

    def _cancel_timer(self, timer):
        """internal api, thread safe

        :param timer:
        :return:
        """
        with self._mutex:
            self._timer_queue.cancel(timer)

    def wakeup(self):
        """

        thread safe
        :return:
        """
        if not self.is_in_loop_thread():
            self.waker.wake()

    def is_in_loop_thread(self):
        """

        thread safe
        :return:
        """
        return threading.get_native_id() == self._tid

    def update_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        events = 0
        if channel.readable():
            events |= select.POLLIN

        if channel.writable():
            events |= select.POLLOUT

        fd = channel.fileno()
        if fd in self._channel_map:
            self._poller.modify(fd, events)
        else:
            self._channel_map[fd] = channel
            self._poller.register(fd, events)

    def remove_channel(self, channel):
        """

        :param channel:
        :return:
        """
        assert self.is_in_loop_thread()

        fd = channel.fileno()
        if fd not in self._channel_map:
            return

        self._channel_map.pop(fd)
        self._poller.unregister(fd)

    def sleep(self, seconds):
        """async sleep seconds, do not block thread"""
        f = Future()

        self.call_later(seconds, lambda: f.set_result(None))

        return f

    def loop(self):
        """

        :return:
        """
        assert self.is_in_loop_thread()

        while True:
            self._resize_timer_queue()

            timeout = self._calc_timeout()

            try:
                events = self._poller.poll(timeout)
            except Exception as e:
                err_code = utils.errno_from_ex(e)
                if err_code != errno.EINTR:
                    break

                events = []

            if events:
                self._handle_events(events)

            self._process_timer_event()

    def _resize_timer_queue(self):
        """resize time queue"""
        # may be cost a lot of time
        self._timer_queue.resize()

    def _calc_timeout(self):
        """

        :return:
        """
        with self._mutex:
            if self._callbacks:
                return 0.0

            timer = self._timer_queue.first()
            if not timer:
                return DEFAULT_TIMEOUT

        timeout = timer.when - self.time()
        return min(max(0.0, timeout), DEFAULT_TIMEOUT)

    def _handle_events(self, events):
        """

        :param events:
        :return:
        """
        for fd, revents in events:
            ev_mask = 0
            if revents & select.POLLIN:
                ev_mask |= io_event.EV_READ

            if revents & select.POLLOUT:
                ev_mask |= io_event.EV_WRITE

            if revents & (select.POLLERR | select.POLLHUP):
                ev_mask |= (io_event.EV_WRITE | io_event.EV_READ)

            channel = self._channel_map[fd]
            channel.handle_events(ev_mask)

    def _process_timer_event(self):
        """

        :return:
        """
        now = self.time()
        with self._mutex:
            callbacks, self._callbacks = self._callbacks, []
            timer_list = self._timer_queue.retrieve(now)

        for cb in callbacks:
            cb.run()

        for timer in timer_list:
            timer.run()
