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
from threading import Thread

from pupdb.core import PupDB

# A group is used as file name, so it must not be able to point anywhere else
GROUP_PATTERN = re.compile(r'[A-Za-z0-9_-]{1,64}')

DAY = 24 * 60 * 60

# How long entries survive on disk at all. Exposed here rather than left as
# a bare default value so ferris.py can cap the days request param at the
# same number – asking for more than this is meaningless, since the data
# simply isn’t retained past it
KEEP_DAYS = 90


def add(group, key, metadata=None):
    db = get_db(group)
    key = str(key)

    # db.get()/db.set() each lock, read or write, and unlock on their own –
    # calling them separately leaves a window between them where a
    # concurrent request for the same key reads the same count this one
    # just did, and both then write back the same incremented value,
    # losing one hit. Held across the whole read-modify-write instead,
    # exactly like get_recent() already does for its own reasons.
    with db.process_lock:
        with open(db.db_file_path, 'r') as db_file:
            database = json.loads(db_file.read())

        entry = database.get(key) or { 'count': 0 }

        if metadata:
            entry['metadata'] = json.loads(metadata) if type(metadata) == str else metadata

        entry['count'] += 1
        entry['last_seen'] = time.time()
        database[key] = entry

        with open(db.db_file_path, 'w') as db_file:
            db_file.write(json.dumps(database))

    return entry


def get(group):
    db = get_db(group)
    return list(db.items())


def get_recent(group, show_days=7, keep_days=KEEP_DAYS):
    db = get_db(group)
    now = time.time()

    # Nothing older than keep_days survives on disk at all, so asking for
    # more than that would just look like an (incorrectly) empty stretch
    # of time rather than actually returning more data
    show_days = min(show_days, keep_days)
    show_after = now - show_days * DAY
    keep_after = now - keep_days * DAY
    recent = []
    kept = {}

    # PupDB has no bulk operation at all: every one of its own get/set/
    # remove calls reads and/or writes the *entire* file. Calling
    # db.remove() once per stale key, as an earlier version of this
    # function did, means one full read+write of the whole file per
    # removed key – for a group with tens of thousands of stale entries
    # (exactly the situation this function exists to clean up) that’s
    # catastrophically slow. Read the file exactly once, decide what
    # survives, and – only if anything actually needs pruning – write
    # the result back exactly once, under the same lock PupDB’s own
    # reads and writes use.
    with db.process_lock:
        with open(db.db_file_path, 'r') as db_file:
            all_entries = json.loads(db_file.read())

        for key, entry in all_entries.items():
            last_seen = entry.get('last_seen', 0)

            # Entries written before this field existed have no
            # last_seen at all, which sorts them as infinitely old,
            # i.e. prune them now too.
            if last_seen < keep_after:
                continue

            kept[key] = entry

            # Anything within show_days is returned regardless of its
            # hit count – a single hit yesterday is still worth
            # showing. Entries older than show_days but not yet as old
            # as keep_days are kept on disk but left out of the
            # response.
            if last_seen >= show_after:
                recent.append((key, entry))

        if len(kept) != len(all_entries):
            with open(db.db_file_path, 'w') as db_file:
                db_file.write(json.dumps(kept))

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

    # Regression check for a lost-update race: db.get()/db.set() each
    # lock and unlock on their own, so calling them as two separate steps
    # let concurrent hits on the same key read the same starting count
    # and overwrite each other’s increment instead of adding up
    hits = 50
    # A previous run of this same script may have left this group
    # non-empty if it failed before reaching the truncate() below
    truncate('race')
    print(f'\nAdding {hits} concurrent hits to the same key in group race:')
    threads = [Thread(target=add, args=('race', 'key')) for _ in range(hits)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    count = get_db('race').get('key')['count']
    print('count:', count)
    assert count == hits, f'Expected {hits}, got {count} instead – add() lost concurrent hits'

    truncate('race')
