#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Tobi Schäfer.
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

from pathlib import Path, PurePath
from base64 import b16encode, b16decode
from datetime import datetime, timedelta, timezone


def add(group, key, metadata=None):
    encoded_key = b16encode(key.encode()).decode()
    path = Path(get_path(group), encoded_key)

    path.mkdir(parents=True, exist_ok=True)

    file_name = datetime.now(timezone.utc).timestamp()
    file = PurePath(path, str(file_name))

    if metadata is None:
        Path(file).touch()
    else:
        Path(file).write_bytes(json.dumps(metadata).encode('utf8'))

    return {
        'key': key,
        'count': len(list(path.glob('*'))),
        'metadata': metadata
    }


def get(group):
    entries = []
    path = get_path(group)

    if not path.exists():
        return entries

    dirs = list(path.glob('*'))

    #days = int(request.args.get('days') or 1)
    #query = client.query(kind='Referrer', ancestor=group_key, order=('-date', '-hits'))
    #query.add_filter('date', '>', datetime.now(timezone.utc) - timedelta(days=days))

    for dir in dirs:
        key = b16decode(dir.name.encode()).decode()
        files = list(dir.glob('*'))

        contents = files[0].read_bytes().decode('utf-8')
        metadata =  json.loads(contents) if contents else None

        entries.append({
            "key": key,
            "count": len(files),
            "metadata": metadata
        })

    return entries


def truncate(group, before_date=None):
    if group == None:
        return

    path = get_path(group)

    if not path.exists():
        return

    def partition(list, size):
        for i in range(0, len(list), size):
            yield list[i : i + size]

    def remove(path):
        if path.is_dir():
            files = list(path.glob('*'))

            for file in files:
                remove(file)

            try:
                # Directory could be non-empty if before_date is set
                path.rmdir()
            except:
                None
        else:
            if before_date:
                date = datetime.fromtimestamp(float(path.name), timezone.utc)

                if before_date < date:
                    path.unlink()
            else:
                path.unlink()

    remove(path)
    return len(list(path.glob('*')))


def get_path(group):
    encoded_group = b16encode(group.encode()).decode()
    return Path('.entrecote', encoded_group)


if __name__ == '__main__':
    print('Adding first entry to group foo:')
    print(add('foo', 'bar'))

    print('\nAdding second entry to group foo:')
    print(add('foo', 'baz'))

    print('\nAdding third entry with same key to group foo:')
    print(add('foo', 'baz'))

    print('\nAdding first entry to group bar with metadata:')
    print(add('bar', 'foo', {'baz': {'fob': 1}}))

    print('\nAll entries of group foo:')
    print(get('foo'))

    print('\nAll entries of group bar:')
    print(get('bar'))

    print('\nTruncating group foo:', truncate('foo'))
    print('Truncating group bar:', truncate('bar'))
