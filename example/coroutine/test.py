# coding: utf-8

import libreactor


loop = libreactor.get_event_loop()


@libreactor.coroutine
def func():

    fut = loop.create_future()
    loop.call_later(4, libreactor.future_set_result, fut, None)
    yield fut

    print("ok")
    return "data"


loop.create_task(func())

loop.run_forever()
