# coding: utf-8

import asyncio
from concurrent import futures

Future = asyncio.Future

future_list = (Future, futures.Future)


def is_future(f):

    return isinstance(f, future_list)
