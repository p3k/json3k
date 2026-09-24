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
import re
import time

from pathlib import Path
from pupdb.core import PupDB

# A group is used as file name, so it must not be able to point anywhere else
GROUP_PATTERN = re.compile(r'[A-Za-z0-9_-]{1,64}')

DAY = 24 * 60 * 60


def add(group, key, metadata=None):
    db = get_db(group)
    entry = db.get(key)

    if not entry:
        entry = { 'count': 0 }

    if metadata:
        entry['metadata'] = json.loads(metadata) if type(metadata) == str else metadata

    entry['count'] += 1
    entry['last_seen'] = time.time()
    db.set(key, entry)
    return entry


def get(group):
    db = get_db(group)
    return list(db.items())


def get_recent(group, show_days=7, keep_days=30):
    db = get_db(group)
    now = time.time()
    show_after = now - show_days * DAY
    keep_after = now - keep_days * DAY
    recent = []

    # A single pass over everything: entries older than keep_days are
    # gone for good (this is what replaces having to truncate the whole
    # group by hand once it gets tedious to load), entries older than
    # show_days but not yet that old are kept on disk but left out of
    # the response, and anything within show_days is returned regardless
    # of its hit count — a single hit yesterday is still worth showing.
    # Entries written before this field existed have no last_seen at
    # all, which sorts them as infinitely old, i.e. prune them now too.
    for key, entry in db.items():
        last_seen = entry.get('last_seen', 0)

        if last_seen < keep_after:
            db.remove(key)
        elif last_seen >= show_after:
            recent.append((key, entry))

    return recent


def truncate(group, before_date=None):
    db = get_db(group)
    return db.truncate_db()


def is_valid_group(group):
    return isinstance(group, str) and GROUP_PATTERN.fullmatch(group) is not None


def get_db(group):
    if not is_valid_group(group):
        raise ValueError('Invalid group name')

    db_path = Path('.entrecote')

    if not db_path.is_dir():
        db_path.mkdir()

    return PupDB(Path(db_path, group + '.json').as_posix())


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

    print('\nRecent entries of group foo (just added, so all of them):')
    print(get_recent('foo'))

    print('\nTruncating group foo:', truncate('foo'))
    print('Truncating group bar:', truncate('bar'))
