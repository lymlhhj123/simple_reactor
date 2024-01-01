# coding: utf-8

from urllib.parse import (
    urlsplit,
    urlunsplit,
    urlencode,
)

from http.cookies import SimpleCookie, Morsel

from .ci_dict import CIDict
from .basic_auth import BasicAuth
from . import utils
from . import const
from .. import errors
from .form_data import FormData


class Request(object):

    DEFAULT_HEADERS = {
        const.ACCEPT_ENCODING: ', '.join(('gzip', 'deflate')),
        const.ACCEPT: '*/*',
        const.CONNECTION: 'keep-alive',
    }

    def __init__(self, method, url, *,
                 headers=None, params=None, data=None, json=None,
                 files=None, auth=None, cookies=None):

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
        self.update_body(data, json, files)

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
            raise errors.InvalidURL(f"Invalid URL {url}: No schema supplied.")

        if scheme not in {const.HTTP, const.HTTPS}:
            raise errors.InvalidURL(f"Invalid URL {url}: unknown scheme {scheme}.")

        netloc = url_parsed.netloc
        host = url_parsed.hostname
        if not netloc or not host:
            raise errors.InvalidURL(f"Invalid URL {url}: No netloc supplied.")

        try:
            netloc.encode("idna").decode("utf-8")
            host.encode("idna").decode("utf-8")
        except UnicodeError:
            raise errors.InvalidURL(f"URL has invalid label: {url}.")

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
        if const.HOST not in self.headers:
            self.headers[const.HOST] = self.host

        # todo: don't compress data for now
        if const.CONTENT_ENCODING in self.headers:
            self.headers.pop(const.CONTENT_ENCODING)

    def update_auth(self, auth):
        """update http auth"""
        if not auth:
            auth = self.auth

        if not auth:
            return

        if isinstance(auth, (list, tuple)):
            auth = BasicAuth(*auth)

        if not isinstance(auth, BasicAuth):
            raise TypeError("BasicAuth() tuple is required")

        self.headers[const.AUTHORIZATION] = auth.encode()

    def update_cookies(self, cookies):
        """update http cookies"""
        if not cookies:
            return

        c = SimpleCookie()
        default = self.headers.pop(const.COOKIE, "")
        c.load(default)

        if isinstance(cookies, dict):
            cookies = cookies.items()

        for k, v in cookies:
            if isinstance(v, Morsel):
                msl_val = v.get(v.key, Morsel())
                msl_val.set(v.key, v.value, v.coded_value)
                c[k] = msl_val
            else:
                c[k] = v

        self.headers[const.COOKIE] = c.output(header="", sep=";").strip()

    def update_body(self, data, json, files):
        """update http body.

        data can be dict, str, bytes;
        json is python dict object;
        files is file object tuple map
        """
        if not data and not json and not files:
            # If the body is None, we set Content-Length: 0 for methods that expect
            # a body (RFC 7230, Section 3.3.2)
            if self.method in const.POST_METHOD:
                self.headers[const.CONTENT_LENGTH] = '0'

            return

        if data and json:
            raise ValueError("`data` and `json` args are mutually exclusive.")

        content_type = None

        if json:
            data = utils.json_dumps(json)
            content_type = "application/json"

        if files:
            data, content_type = self._encode_files(data, files)
            # send form-data by chunked
            self.headers[const.TRANSFER_ENCODING] = "chunked"
        else:
            if hasattr(data, "read"):
                self.headers[const.TRANSFER_ENCODING] = "chunked"
            else:
                if isinstance(data, (dict, list, tuple)):
                    content_type = "application/x-www-form-urlencoded"
                    data = urlencode(data, doseq=True, encoding="utf-8")

                if isinstance(data, str):
                    data = data.encode("utf-8")

                if not isinstance(data, bytes):
                    raise TypeError(f"request body must be bytes, not {type(data)}")

                self.headers[const.CONTENT_LENGTH] = len(data)

        self.body = data

        # Add content-type if it wasn't explicitly provided.
        if const.CONTENT_TYPE not in self.headers:
            content_type = content_type if content_type else "application/octet-stream"
            self.headers[const.CONTENT_TYPE] = content_type

    @staticmethod
    def _encode_files(data, files):
        """encode form data body

        :param data: dict or tuple of list, example: {key: value} or [(key, value), (key1, value1)]
        :param files: dict of file tuple, example: {name: (filename, file_data, content_type, headers)}
                      content_type and headers is optional
        """
        if data and not isinstance(data, (dict, list, tuple)):
            raise TypeError("data type must be (dict, list, tuple)")

        data = utils.to_key_value_list(data or {})
        files = utils.to_key_value_list(files or {})

        form_data = FormData()

        for name, value in data:
            form_data.add(name, value)

        for name, file_tuple in files:
            content_type = None
            custom_headers = None
            if len(file_tuple) == 2:
                file_name, file_data = file_tuple
            elif len(file_tuple) == 3:
                file_name, file_data, content_type = file_tuple
            else:
                file_name, file_data, content_type, custom_headers = file_tuple

            form_data.add(name, file_data, file_name, content_type, custom_headers)

        content_type = f"multipart/form-data; boundary={form_data.boundary()}"

        return form_data, content_type
