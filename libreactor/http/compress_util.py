# coding: utf-8

import zlib


class ZibDecompressor(object):

    def __init__(self, encoding, *, loop):

        if encoding == "gzip":
            mode = 16 + zlib.MAX_WBITS
        else:
            mode = -zlib.MAX_WBITS

        self._decompress = zlib.decompressobj(wbits=mode)
        self._loop = loop

    async def decompress(self, data, max_length=0):
        """decompress response body"""
        return await self._loop.run_in_executor(self._decompress.decompress, data, max_length)
