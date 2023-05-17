# coding: utf-8

from libreactor import EventLoop
from libreactor import TaskScheduler


ev = EventLoop.current()

task_scheduler = TaskScheduler(ev)

task_scheduler.call_later()