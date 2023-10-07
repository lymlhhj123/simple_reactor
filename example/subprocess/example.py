# coding: utf-8

from libreactor import get_event_loop
from libreactor import Subprocess


def on_result(status, stdout, stderr):
    """

    :param status:
    :param stdout:
    :param stderr:
    :return:
    """
    print(status, "stdout: ", stdout, "stderr: ", stderr)


ev = get_event_loop()

Subprocess("uname -a", ev, on_result)

ev.loop()
