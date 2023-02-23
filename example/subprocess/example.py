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
    print(status, stdout, stderr)


ev = EventLoop()

Popen(ev, "ls -al", on_result=on_result)

ev.loop()
