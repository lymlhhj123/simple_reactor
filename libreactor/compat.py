# coding: utf-8


def asyncio_loop_adapter(loop_cls):

    def get_debug(self):
        """asyncio.Future require this method"""
        return 0

    def call_exception_handler(self, context):
        """asyncio.Future require this method"""

    setattr(loop_cls, "get_debug", get_debug)
    setattr(loop_cls, "call_exception_handler", call_exception_handler)

    return loop_cls
