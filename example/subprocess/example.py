# coding: utf-8

from libreactor.event_loop import EventLoop
from libreactor.subprocess import Popen


def on_result(status, stdout, stderr):
    """

    :param status:
    :param stdout:
    :param stderr:
    :return:
    """
    print(status, "stdout: ", stdout, "stderr: ", stderr)


ev = EventLoop()

Popen(ev, "uname -a", on_result=on_result)

ev.loop()
