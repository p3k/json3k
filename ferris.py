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

import entrecote
import json

from datetime import datetime, timedelta, timezone
from gzip import compress
from wsgiref.handlers import format_date_time

# An arbitrary but generous sanity bound on the days query parameter, well
# past entrecote's own keep_days default — keeps a stray or malicious value
# (days=999999999) from being accepted as well-formed input
MAX_DAYS = 365

def ferris(request, make_response):
    response_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    group = request.args.get('group')

    if not entrecote.is_valid_group(group):
        return make_response('', 400)

    key = request.args.get('url')
    callback = request.args.get('callback')

    if key:
        metadata = request.args.get('metadata')

        try:
            entry = entrecote.add(group, key, metadata)
        except ValueError:
            # The metadata is not valid JSON
            return make_response('', 400)

        return make_response(str(entry['count']), 201)

    else:
        days = request.args.get('days')

        if days is not None:
            try:
                days = int(days)
            except ValueError:
                return make_response('', 400)

            if not 1 <= days <= MAX_DAYS:
                return make_response('', 400)

        recent = entrecote.get_recent(group, days) if days is not None else entrecote.get_recent(group)

        referrers = sorted(
            map(
                lambda entry: {
                    'url': entry[0],
                    'hits': entry[1]['count'],
                    'metadata': entry[1]['metadata'] if 'metadata' in entry[1] else {}
                },
                recent
            ),
            key=lambda entry: entry['hits'],
            reverse=True
        )

        # Let the browser cache the referrer list for 10 minutes
        response_headers['Expires'] = format_date_time(datetime.now(timezone.utc).timestamp() + 600)

        data = json.dumps(list(referrers))

        if callback:
            data = '%s(%s)' % (callback, data)
            response_headers['Content-Type'] = 'application/javascript'

        if request.headers.get('Accept-Encoding', '').find('gzip') > -1:
            response_headers['Content-Encoding'] = 'gzip'
            data = compress(data.encode('utf-8'))

        response = make_response(data)
        response.headers = response_headers

        return response


def cleanup(request, make_response):
    if request.remote_addr != '127.0.0.1':
        return make_response('', 401)

    group = request.args.get('group')

    if not entrecote.is_valid_group(group):
        return make_response('', 400)

    return str(entrecote.truncate(group))
