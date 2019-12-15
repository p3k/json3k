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
import traceback

from datetime import datetime, timedelta, timezone
from gzip import compress, decompress
from io import StringIO
from sys import exc_info

from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from google.cloud import datastore

client = datastore.Client()


def get_url(url, request_headers):
    content = ''
    headers = {}

    try:
        request = Request(url, None, request_headers)
        response = urlopen(request)

        headers.update(response.headers)

        headers['X-Roxy-Url'] = response.geturl()
        headers['X-Roxy-Status'] = response.status

        if response.headers.get('Content-Encoding') == 'gzip':
            content = decompress(response.read())
        else:
            content = response.read()

    except HTTPError as error:
        headers['X-Roxy-Status'] = error.getcode()
        headers['X-Roxy-Error'] = error.msg

    except:
        traceback.print_exc()
        message = str(exc_info()[1])

        headers['X-Roxy-Status'] = 500
        headers['X-Roxy-Error'] = message

    else:
        content_type = headers['Content-Type']

        if content_type and (content_type.startswith('text/') or
                             content_type.startswith('application/') or
                             content_type.endswith('xml')):
            try:
                content = content.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = content.decode('iso-8859-1')

    return {'content': content, 'headers': headers}


def roxy(request, make_response):
    TTL = 60

    url = request.args.get('url')
    callback = request.args.get('callback')

    if not url:
        return make_response('', 400)

    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }

    key = client.key('Resource', url)
    resource = client.get(key)

    if resource is None:
        resource = datastore.Entity(key=key, exclude_from_indexes=[
                                    'content', 'headers', 'date'])
        resource.update(date=datetime(
            1, 1, 1, tzinfo=timezone.utc), content='', headers={})

    if datetime.now(timezone.utc) - resource['date'] > timedelta(seconds=TTL):
        response = get_url(url, {
            'Accept-Encoding': 'gzip, deflate',
            'If-None-Match': resource['headers'].get('etag', ''),
            'Cookie': urlencode(request.cookies),
            'User-Agent': str(request.user_agent),
            'Referer': request.referrer or ''
        })

        response_headers['X-Roxy-Debug'] = 'Fetched from URL'

        resource.update({
            'headers': response.get('headers'),
            'content': response.get('content'),
            'date': datetime.now(timezone.utc)
        })

        client.put(resource)

    else:
        response_headers['X-Roxy-Debug'] = 'Fetched from Datastore'

    data = json.dumps({
        'headers': resource['headers'],
        'content': resource['content']
    })

    if callback:
        response_headers['Content-Type'] = 'application/javascript'
        data = '%s(%s)' % (callback, data)

    if request.headers.get('Accept-Encoding', '').find('gzip') > -1:
        response_headers['Content-Encoding'] = 'gzip'
        data = compress(data.encode('utf-8'))

    response = make_response(data)
    response.headers = response_headers

    return response
