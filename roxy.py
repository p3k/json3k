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
from io import StringIO
from sys import exc_info
from wsgiref.handlers import format_date_time

from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlencode


def get_url(url, request_headers):
    content = ''
    message = ''
    headers = {}
    status = 200

    try:
        request = Request(url, None, request_headers)
        response = urlopen(request, None, 3)

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

    except:
        traceback.print_exc()
        status = headers['X-Roxy-Status'] = 500
        message = headers['X-Roxy-Error'] = str(exc_info()[1])

    else:
        content_type = headers.get('Content-Type')

        if content_type and (content_type.startswith('text/') or
                             content_type.startswith('application/') or
                             content_type.endswith('xml')):
            try:
                content = content.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = content.decode('iso-8859-1')

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

    set_header('Accept', request.headers.get('Accept'))
    set_header('Cookie', urlencode(request.cookies) or None)
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
        if key in ['Content-Length', 'Transfer-Encoding']: continue

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
