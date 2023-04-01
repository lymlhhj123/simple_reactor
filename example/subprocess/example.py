# coding: utf-8

from libreactor import EventLoop
from libreactor import Subprocess


def on_result(status, stdout, stderr):
    """

    :param status:
    :param stdout:
    :param stderr:
    :return:
    """
    print(status, "stdout: ", stdout, "stderr: ", stderr)


ev = EventLoop.current()

Subprocess("uname -a", ev, on_result)

ev.loop()
