# coding: utf-8

import json
from urllib.parse import (
    urlsplit,
    urlunsplit,
)

from http.cookies import SimpleCookie, Morsel

from .ci_dict import CIDict
from .basic_auth import Auth, BasicAuth
from . import utils
from . import const


class Request(object):

    DEFAULT_HEADERS = {
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }

    def __init__(self, method, url, *,
                 headers=None, params=None,
                 data=None, auth=None, cookies=None):

        self.method = None
        self.url = None
        self.params = params or {}
        self.host = None
        self.path = None

        self.auth = None
        self.headers = None
        self.auth = None
        self.body = None

        self.update_method(method)
        self.update_url(url, params or {})
        self.update_headers(headers or {})
        self.update_auth(auth)
        self.update_cookies(cookies)
        self.update_body(data)

    def update_method(self, method):
        """update http method"""
        utils.validate_method(method)
        self.method = method.upper()

    def update_url(self, url, params):
        """update http url"""
        utils.validate_path(url)

        url_parsed = urlsplit(url)

        scheme = url_parsed.scheme
        if not scheme:
            raise ValueError(f"Invalid URL {url}: No schema supplied. Perhaps you meant http://{url}?")

        if scheme not in {const.HTTP, const.HTTPS}:
            raise ValueError(f"Invalid URL {url}: unknown scheme {scheme}")

        netloc = url_parsed.netloc
        host = url_parsed.hostname
        if not netloc or not host:
            raise ValueError(f"Invalid URL {url}: No netloc supplied")

        try:
            netloc.encode("idna").decode("utf-8")
            host.encode("idna").decode("utf-8")
        except UnicodeError:
            raise ValueError(f"URL has invalid label: {url}")

        query = url_parsed.query
        encode_str = utils.encode_params(params)
        if encode_str:
            if query:
                query = f'{query}&{encode_str}'
            else:
                query = encode_str

        path = url_parsed.path
        if not path:
            path = "/"

        fragment = url_parsed.fragment

        path = urlunsplit(["", "", path, query, fragment])
        self.path = utils.requote_uri(path)

        self.url = urlunsplit([scheme, netloc, path, query, fragment])

        login, password = url_parsed.username, url_parsed.password
        if login:
            self.auth = BasicAuth(login, password or "")

    def update_headers(self, headers):
        """update http headers"""

        self.headers = CIDict()

        for header, value in headers.items():
            utils.validate_header_name(header)
            utils.validate_header_value(value)

            self.headers[utils.to_native_string(header)] = value

        for hdr, value in self.DEFAULT_HEADERS.items():
            if hdr not in self.headers:
                self.headers[hdr] = value

        # set host
        if "Host" not in self.headers:
            self.headers["Host"] = self.host

        # set default content-type
        if self.method in const.POST_METHOD and "content-type" not in self.headers:
            self.headers["content-type"] = "application/octet-stream"

        # set the connection header
        if "connection" not in self.headers:
            self.headers["connection"] = "keep-alive"

    def update_auth(self, auth):
        """update http auth"""
        if not auth:
            auth = self.auth

        if not auth:
            return

        if not isinstance(auth, Auth):
            raise TypeError("require type Auth()")

        self.headers["Authorization"] = auth.encode()

    def update_cookies(self, cookies):
        """update http cookies"""
        if not cookies:
            return

        c = SimpleCookie()
        default = self.headers.pop("cookie", "")
        c.load(default)

        for k, v in cookies.items():
            if isinstance(v, Morsel):
                msl_val = v.get(v.key, Morsel())
                msl_val.set(v.key, v.value, v.coded_value)
                c[k] = msl_val
            else:
                c[k] = v

        self.headers["cookie"] = c.output(header="", sep=";").strip()

    def update_body(self, data):
        """update http body. data can be dict, str, bytes or file"""
        if not data:
            return

        if isinstance(data, dict):
            data = json.dumps(data)

        if isinstance(data, str):
            data = data.encode("utf-8")

        if isinstance(data, (str, bytes, bytearray)):
            self.body = data
        else:
            pass
