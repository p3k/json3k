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

from datetime import datetime, timedelta, timezone
from wsgiref.handlers import format_date_time
from gzip import compress

from google.cloud import datastore

client = datastore.Client()


def ferris(request, make_response):
    response_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    group = request.args.get('group')

    if not group:
        return make_response('', 400)

    url = request.args.get('url')
    callback = request.args.get('callback')

    if url:
        key = client.key('Group', group, 'Referrer', url)
        referrer = client.get(key=key)

        if referrer is None:
            referrer = datastore.Entity(key=key, exclude_from_indexes=['metadata'])
            referrer.update(date=datetime.now(timezone.utc), hits=0, metadata={})

        referrer['hits'] += 1
        metadata = request.args.get('metadata')

        if metadata:
            try:
                referrer['metadata'].update(json.loads(metadata))
            except Exception as error:
                print(error)

        client.put(referrer)

        return make_response(str(referrer['hits']), 201)

    else:
        days = int(request.args.get('days') or 1)
        group_key = client.key('Group', group)

        query = client.query(kind='Referrer', ancestor=group_key, order=('-date', '-hits'))
        query.add_filter('date', '>', datetime.now(timezone.utc) - timedelta(days=days))

        records = query.fetch()

        referrers = map(lambda entity: {
            'url': entity.key.name,
            'hits': entity['hits'],
            'date': entity['date'].timestamp() * 1000,
            'metadata': entity['metadata']
        }, records)

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
    if request.remote_addr != '127.0.0.1' and request.headers.get('X-Appengine-Cron') != 'true':
        return make_response('', 401)

    def partition(list, size):
        for i in range(0, len(list), size):
            yield list[i : i + size]

    query = client.query(kind='Referrer')
    query.keys_only()

    keys = list(record.key for record in query.fetch())

    for batch in partition(keys, 500):
        client.delete_multi(batch)

    return str(len(keys))
