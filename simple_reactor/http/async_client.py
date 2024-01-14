# coding: utf-8

from urllib.parse import urlsplit

from .request import Request
from .connection import Connection
from ..protocols import IOStream
from ..options import (
    Options,
    SSLOptions
)
from . import const
from .. import errors


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

    async def request(self, method, url, *,
                      params=None, data=None, json=None, files=None,
                      headers=None, cookies=None, auth=None,
                      key_file=None, cert_file=None, verify=True,
                      allow_redirect=True, max_redirects=3, timeout=None):
        """request url and return response

        :param method:
        :param url:
        :param params:
        :param data:
        :param json:
        :param files: dict, name of file tuple,
                      for example: {name: (filename, fileobject or file data, content_type, custom_headers)}
        :param headers:
        :param cookies:
        :param auth:
        :param key_file:
        :param cert_file:
        :param verify:
        :param allow_redirect:
        :param max_redirects:
        :param timeout:
        """
        redirects = 0
        history = []
        while True:
            req = Request(method, url, params=params, headers=headers,
                          data=data, json=json, files=files, cookies=cookies, auth=auth)

            conn = await self._connection_from_url(
                url=req.url,
                verify=verify,
                key_file=key_file,
                cert_file=cert_file,
                timeout=timeout
            )

            try:
                resp = await conn.send_request(req)
                if resp.status_code not in const.REDIRECTS_CODE or not allow_redirect:
                    break

                # handle url redirect
                history.append(resp)
                redirects += 1

                if max_redirects and redirects > max_redirects:
                    raise errors.TooManyRedirects(f"too many redirects, {history}")

                url = resp.headers.get(const.LOCATION) or resp.headers.get(const.URI)
                if not url:
                    break
            finally:
                conn.close()

        resp.request = req
        resp.history = history
        return resp

    async def _connection_from_url(self, url, verify=True, key_file=None, cert_file=None, timeout=None):
        """make http connection from url"""
        parsed = urlsplit(url)
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

        protocol = await self.loop.connect_tcp(hostname, port, proto_factory=IOStream, **kwargs)
        return Connection(protocol)

    def close(self):
        """close http client"""
        pass

    async def __aenter__(self):

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):

        self.close()
