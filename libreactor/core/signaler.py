# coding: utf-8

import os
import threading
import signal

from ..common import fd_helper
from .channel import Channel


class Signaler(object):

    def __init__(self, ev):
        """

        :param ev:
        """
        self.ev = ev

        r, w = fd_helper.make_async_pipe()

        # this function can only be called from the main thread
        assert threading.get_native_id() == os.getpid()

        self.old_fd = signal.set_wakeup_fd(w)

        self.reader = r
        self.channel = Channel(r, ev)

    def install_signal(self, sig_num):
        """

        :param sig_num:
        :return:
        """
        signal.signal(sig_num, lambda *args: None)