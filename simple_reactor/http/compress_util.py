# coding: utf-8

import zlib


def _encoding_to_mode(encoding):

    if encoding == "gzip":
        mode = 16 + zlib.MAX_WBITS
    else:
        mode = -zlib.MAX_WBITS

    return mode


class ZLibCompressor(object):

    def __init__(self, encoding, *, loop, level=None, strategy=zlib.Z_DEFAULT_STRATEGY):

        self.mode = _encoding_to_mode(encoding)
        # -1 is the default level
        level = level if level else -1
        self._compress = zlib.compressobj(wbits=self.mode, level=level, strategy=strategy)
        self._loop = loop

    async def compress(self, data):
        """compress data"""
        return await self._loop.run_in_thread(self._compress.compress, data)


class ZLibDecompressor(object):

    def __init__(self, encoding, *, loop):

        self.mode = _encoding_to_mode(encoding)
        self._decompress = zlib.decompressobj(wbits=self.mode)
        self._loop = loop

    async def decompress(self, data, max_length=0):
        """decompress data"""
        return await self._loop.run_in_thread(self._decompress.decompress, data, max_length)
