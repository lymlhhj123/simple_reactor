# coding: utf-8

import re
from urllib.parse import urlencode


# the patterns for both name and value are more lenient than RFC
# definitions to allow for backwards compatibility
_is_legal_header_name = re.compile(rb'[^:\s][^:\r\n]*').fullmatch
_is_illegal_header_value = re.compile(rb'\n(?![ \t])|\r(?![ \t\n])').search

# These characters are not allowed within HTTP URL paths.
#  See https://tools.ietf.org/html/rfc3986#section-3.3 and the
#  https://tools.ietf.org/html/rfc3986#appendix-A pchar definition.
# Prevents CVE-2019-9740.  Includes control characters such as \r\n.
# We don't restrict chars above \x7f as putrequest() limits us to ASCII.
_contains_disallowed_url_pchar_re = re.compile('[\x00-\x20\x7f]')
# Arguably only these _should_ allowed:
#  _is_allowed_url_pchars_re = re.compile(r"^[/!$&'()*+,;=:@%a-zA-Z0-9._~-]+$")
# We are more lenient for assumed real world compatibility purposes.

# These characters are not allowed within HTTP method names
# to prevent http header injection.
_contains_disallowed_method_pchar_re = re.compile('[\x00-\x1f]')


def to_native_string(string, encoding='ascii'):
    """Given a string object, regardless of type, returns a representation of
    that string in the native string type, encoding and decoding where
    necessary. This assumes ASCII unless told otherwise.
    """
    if isinstance(string, str):
        out = string
    else:
        out = string.decode(encoding)

    return out


def validate_method(method):
    """Validate a method name"""
    # prevent http header injection
    match = _contains_disallowed_method_pchar_re.search(method)
    if match:
        raise ValueError(
                f"method can't contain control characters. {method!r} "
                f"(found at least {match.group()!r})")


def validate_path(url):
    """Validate a url for putrequest."""
    # Prevent CVE-2019-9740.
    match = _contains_disallowed_url_pchar_re.search(url)
    if match:
        raise ValueError(f"URL can't contain control characters. {url!r} "
                         f"(found at least {match.group()!r})")


def validate_host(host):
    """Validate a host so it doesn't contain control characters."""
    # Prevent CVE-2019-18348.
    match = _contains_disallowed_url_pchar_re.search(host)
    if match:
        raise ValueError(f"URL can't contain control characters. {host!r} "
                         f"(found at least {match.group()!r})")


def validate_header_name(header):
    """Validate a header name"""
    if not _is_legal_header_name(header):
        raise ValueError(f'Invalid header name {header}')


def validate_header_value(value):
    """Validate a header value"""
    if _is_illegal_header_value(value):
        raise ValueError(f'Invalid header value {value}')


def encode_params(params):
    """Encode parameters in a piece of data."""
    if isinstance(params, (str, bytes)):
        return params
    else:
        return urlencode(params)


def unquote_unreserved(uri):
    """Un-escape any percent-escape sequences in a URI that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.

    :rtype: str
    """
    parts = uri.split('%')
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            try:
                c = chr(int(h, 16))
            except ValueError:
                raise InvalidURL("Invalid percent-escape sequence: '%s'" % h)

            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = '%' + parts[i]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote_uri(uri):
    """Re-quote the given URI.

    This function passes the given URI through an unquote/quote cycle to
    ensure that it is fully and consistently quoted.

    :rtype: str
    """
    safe_with_percent = "!#$%&'()*+,/:;=?@[]~"
    safe_without_percent = "!#$&'()*+,/:;=?@[]~"
    try:
        # Unquote only the unreserved characters
        # Then quote only illegal characters (do not quote reserved,
        # unreserved, or '%')
        return quote(unquote_unreserved(uri), safe=safe_with_percent)
    except InvalidURL:
        # We couldn't unquote the given URI, so let's try quoting it, but
        # there may be unquoted '%'s in the URI. We need to make sure they're
        # properly quoted so they do not cause issues elsewhere.
        return quote(uri, safe=safe_without_percent)
