#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Tobi Schäfer.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re
import traceback

from datetime import datetime, timedelta, timezone
from gzip import compress, decompress
from http.client import HTTPConnection, HTTPSConnection
from io import StringIO
from ipaddress import ip_address
from socket import SOCK_STREAM, create_connection, getaddrinfo
from sys import exc_info
from wsgiref.handlers import format_date_time

from urllib.error import HTTPError
from urllib.request import (
    HTTPDefaultErrorHandler,
    HTTPErrorProcessor,
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    UnknownHandler
)
# Local settings are optional, see `local.py` in the README
try:
    from local import allow_private_hosts
except ImportError:
    allow_private_hosts = False


# The headers of the proxied response that are passed on with the response of
# Roxy. Any other would take effect on the origin of the proxy: `Set-Cookie`
# could set its cookies, `Strict-Transport-Security` or `Clear-Site-Data`
# would apply to it, and `Cache-Control` would undo the caching set by Roxy
PASSED_HEADERS = ('etag', 'last-modified')


def is_passed_header(name):
    name = name.lower()
    return name in PASSED_HEADERS or name.startswith('x-roxy-')


class ForbiddenUrl(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# An XML document’s declared encoding, which must be within its very first
# bytes if present at all
XML_ENCODING_PATTERN = re.compile(rb'^\s*<\?xml[^>]*\bencoding=["\']([^"\']+)["\']')


def get_declared_charset(content_type, content):
    # The transport-level charset, when given, takes priority over the
    # document’s own encoding declaration
    if content_type:
        match = re.search(r';\s*charset=["\']?([^;"\'\s]+)', content_type, re.IGNORECASE)

        if match:
            return match.group(1)

    match = XML_ENCODING_PATTERN.match(content[:200])

    if match:
        return match.group(1).decode('ascii', 'ignore')

    return None


def decode_content(content, content_type):
    # Neither a bogus declared charset nor a feed that isn’t actually UTF-8
    # should make this raise; Latin-1 never fails to decode, so it is always
    # the last resort, not the first guess
    for charset in (get_declared_charset(content_type, content), 'utf-8-sig'):
        if not charset:
            continue

        try:
            return content.decode(charset)
        except (LookupError, UnicodeDecodeError):
            pass

    return content.decode('iso-8859-1')


def check_scheme(request):
    # Rely on the request’s own URL parsing to avoid any mismatch with what is opened eventually
    if request.type not in ('http', 'https'):
        raise ForbiddenUrl(400, 'Only http and https URLs are supported')


def is_public(address):
    ip = ip_address(address.partition('%')[0])

    # Look at the embedded IPv4 address of IPv4-mapped addresses like `::ffff:127.0.0.1`
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    return ip.is_global


def create_public_connection(address, *args, **kwargs):
    host, port = address
    addresses = [info[4][0] for info in getaddrinfo(host, port, type=SOCK_STREAM)]

    if not allow_private_hosts and not all(map(is_public, addresses)):
        raise ForbiddenUrl(403, 'Requests to non-public addresses are not allowed')

    error = None

    # Connect to the addresses just checked instead of resolving the host name a
    # second time, so DNS rebinding cannot sneak in a different address
    for ip in addresses:
        try:
            return create_connection((ip, port), *args, **kwargs)
        except OSError as exc:
            error = exc

    raise error


class PublicHTTPConnection(HTTPConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = create_public_connection


class PublicHTTPSConnection(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = create_public_connection


class PublicHTTPHandler(HTTPHandler):
    def do_open(self, http_class, req, **http_conn_args):
        return super().do_open(PublicHTTPConnection, req, **http_conn_args)


class PublicHTTPSHandler(HTTPSHandler):
    def do_open(self, http_class, req, **http_conn_args):
        return super().do_open(PublicHTTPSConnection, req, **http_conn_args)


class PublicRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        request = super().redirect_request(*args, **kwargs)

        if request:
            check_scheme(request)

        return request


# Unlike `urllib.request.urlopen` this opener has neither a file, FTP nor data
# handler, and every connection – including those following a redirect – goes
# through `create_public_connection`
opener = OpenerDirector()

for handler in (
    ProxyHandler(),
    UnknownHandler(),
    PublicHTTPHandler(),
    PublicHTTPSHandler(),
    PublicRedirectHandler(),
    HTTPDefaultErrorHandler(),
    HTTPErrorProcessor()
):
    opener.add_handler(handler)


def get_url(url, request_headers):
    content = ''
    message = ''
    headers = {}
    status = 200

    try:
        request = Request(url, None, request_headers)
        check_scheme(request)
        response = opener.open(request, None, 3)

        headers.update(response.headers)

        url = headers['X-Roxy-Url'] = response.geturl()
        status = headers['X-Roxy-Status'] = response.status

        etag = headers.get('ETag')

        if etag:
            # Remove suffix like `-gzip` from etag to make it work
            headers['ETag'] = re.sub('-[^"]+("?)$', '\\1', etag)

        if response.headers.get('Content-Encoding') == 'gzip':
            content = decompress(response.read())
        else:
            content = response.read()

    except HTTPError as error:
        status = headers['X-Roxy-Status'] = error.getcode()
        message = headers['X-Roxy-Error'] = error.msg

    except ForbiddenUrl as error:
        status = headers['X-Roxy-Status'] = error.status
        message = headers['X-Roxy-Error'] = str(error)

    except:
        #traceback.print_exc()
        status = headers['X-Roxy-Status'] = 500
        message = headers['X-Roxy-Error'] = str(exc_info()[1])

    else:
        content_type = headers.get('Content-Type')

        if content_type and (content_type.startswith('text/') or
                             content_type.startswith('application/') or
                             content_type.endswith('xml')):
            content = decode_content(content, content_type)

    return {
        'status': status,
        'content': content,
        'headers': headers,
        'message': message,
        'url': url
    }


def roxy(request, make_response):
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }

    def send_response(status = 200, headers = {}, content = ''):
        response = make_response(content, status)
        response.headers = headers
        return response

    url = request.args.get('url')
    callback = request.args.get('callback')

    if not url:
        return send_response(400, response_headers)

    content = None
    now = datetime.now(timezone.utc)

    resource = {
        'content': '',
        'date': now,
        'headers': {},
        'status': 200
    }

    headers = { 'Accept-Encoding': 'gzip, deflate' }

    def set_header(header_name, value):
        if value:
            headers[header_name] = value

    # The cookies of the client belong to the origin of the proxy, so they must
    # not be sent to any other server
    set_header('Accept', request.headers.get('Accept'))
    set_header('Referer', request.referrer)
    set_header('User-Agent', str(request.user_agent))

    data = get_url(url, headers)
    content = data.get('content')

    if content: resource['content'] = content

    resource.update({
        'headers': data.get('headers'),
        'status': data.get('status')
    })

    for key in resource['headers']:
        if is_passed_header(key):
            response_headers.setdefault(key, resource['headers'].get(key))

    response_headers['Expires'] = format_date_time(now.timestamp() + 60)

    data = ''
    content = None
    status = resource.get('status') or 200

    if request.method == 'GET':
        content = resource.get('content')

        try:
            content = content.decode('utf-8')
        except:
            pass

        data = json.dumps({
            'content': content,
            'headers': resource.get('headers')
        })

        if status == 304:
            # If request was unconditional we need to return 200 with content no matter what
            for key in request.headers.keys():
                if key.startswith('If-'): continue
                status = 200
                break

    if callback:
        response_headers['Content-Type'] = 'application/javascript'
        data = '%s(%s)' % (callback, data)

    if request.headers.get('Accept-Encoding', '').find('gzip') > -1:
        response_headers['Content-Encoding'] = 'gzip'
        data = compress(data.encode('utf-8'))

    return send_response(status, response_headers, data)
