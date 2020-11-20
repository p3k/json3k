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
from pupdb.core import PupDB


def add(group, key, metadata=None):
    db = get_db(group)
    entry = db.get(key)

    if not entry:
        entry = { 'count': 0 }

    if metadata:
        entry['metadata'] = json.loads(metadata) if type(metadata) == str else metadata

    entry['count'] += 1
    db.set(key, entry)
    return entry


def get(group):
    db = get_db(group)
    return list(db.items())


def truncate(group, before_date=None):
    db = get_db(group)
    return db.truncate_db()


def get_db(group):
    return PupDB('.db-' + group + '.json')


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
