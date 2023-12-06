# coding: utf-8

from urllib.parse import urlsplit

from .request import Request
from .connection import Connection
from ..protocols import StreamReceiver
from ..options import (
    Options,
    SSLOptions
)
from . import const


class AsyncClient(object):

    def __init__(self, *, loop):

        self.loop = loop

    async def get(self, url, *, params=None, **kwargs):
        """http get method"""
        resp = await self.request(const.METH_GET, url, params=params, **kwargs)
        return resp

    async def post(self, url, *, data=None, **kwargs):
        """http post method"""
        resp = await self.request(const.METH_POST, url, data=data, **kwargs)
        return resp

    async def head(self, url, **kwargs):
        """http head method"""
        resp = await self.request(const.METH_HEAD, url, **kwargs)
        return resp

    async def put(self, url, *, data=None, **kwargs):
        """http put method"""
        resp = await self.request(const.METH_PUT, url, data=data, **kwargs)
        return resp

    async def delete(self, url, **kwargs):
        """http delete method"""
        resp = await self.request(const.METH_DELETE, url, **kwargs)
        return resp

    async def patch(self, url, **kwargs):
        """http patch method"""
        resp = await self.request(const.METH_PATCH, url, **kwargs)
        return resp

    async def options(self, url, **kwargs):
        """http options method"""
        resp = await self.request(const.METH_OPTIONS, url, **kwargs)
        return resp

    async def trace(self, url, **kwargs):
        """http trace method"""
        resp = await self.request(const.METH_TRACE, url, **kwargs)
        return resp

    async def request(self, method, url, *, params=None, data=None,
                      headers=None, cookies=None, auth=None, key_file=None,
                      cert_file=None, verify=True, allow_redirect=True, timeout=None):
        """request url"""
        req = Request(method, url, params=params, headers=headers,
                      data=data, cookies=cookies, auth=auth)

        conn = await self._connection_from_request(
            req=req,
            verify=verify,
            key_file=key_file,
            cert_file=cert_file,
            timeout=timeout
        )

        try:
            await conn.send_request(req)
            resp = await conn.get_response()
            resp.request = req
        finally:
            conn.close()

        return resp

    async def _connection_from_request(self, req, verify=True, key_file=None, cert_file=None, timeout=None):
        """make http connection from http request"""
        parsed = urlsplit(req.url)
        hostname = parsed.hostname
        port = parsed.port

        if not port:
            port = const.HTTP_PORT if parsed.scheme == const.HTTP else const.HTTPS_PORT

        kwargs = {}

        options = Options()
        options.connect_timeout = timeout
        kwargs["options"] = options

        if parsed.scheme == const.HTTPS and verify is True:
            ssl_options = SSLOptions()
            ssl_options.server_hostname = hostname
            ssl_options.key_file = key_file
            ssl_options.cert_file = cert_file

            kwargs["ssl_options"] = ssl_options

        stream = await self.loop.connect_tcp(hostname, port, proto_factory=StreamReceiver, **kwargs)
        return Connection(stream)

    def close(self):
        """"""
        pass
