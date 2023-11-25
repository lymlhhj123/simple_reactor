# coding: utf-8

import signal

from . import fd_helper
from .common import process_info
from .channel import Channel


class Signaler(object):
    """
    this class can only be used in main thread
    """

    def __init__(self, loop, signal_nums):

        self.sig_nums = signal_nums

        r, w = fd_helper.make_async_pipe()

        assert process_info.is_main_thread()

        self._install(w)

        self.reader = r
        self.channel = Channel(r, loop)
        self.channel.set_read_callback(self._handle_read)
        self.channel.enable_reading()

    def _install(self, w):

        for sig in self.sig_nums:
            signal.signal(sig, lambda *args: None)
            signal.siginterrupt(sig, False)

        signal.set_wakeup_fd(w)

    def _handle_read(self, chan):
        """called when signal received"""

    def _signal_received(self, sig_num):
        """called when a signal received"""

    def fileno(self):

        return self.reader
