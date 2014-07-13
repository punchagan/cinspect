from __future__ import absolute_import, print_function

import json
from os.path import exists


def read_index(db):
    """ Read the index and return the data.

    Returns an empty dictionary if no index exists.

    """

    if exists(db):
        with open(db) as f:
            data = json.load(f)
    else:
        data = {}

    return data

def write_index(db, data):
    """ Read the index and return the data. """

    with open(db, 'w') as f:
        json.dump(data, f, indent=2)
