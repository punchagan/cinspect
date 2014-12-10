from __future__ import absolute_import, print_function

import glob
# fixme: it might be better to use an sqlitedb instead
import json
from os.path import basename, exists, expanduser, join
import re
import sys

from pkg_resources import parse_version


def get_index_path(version=None, only_existing=False, allow_similar=True):
    """Return the path to the index file for the given version.

    If only_existing is True, checks if the db file exists.  An error is raised
    if allow_similar is False.  If file doesn't exist and allow_similar is
    True, the closest matching version's db is returned.

    """

    if version is None:
        version = _get_current_version()

    path_ = path = expanduser(join('~/.cinspect', 'index-%s.json' % version))
    if only_existing and not exists(path):
       if allow_similar:
           files = glob.glob(expanduser(join('~/.cinspect', 'index*.json')))
           path = _get_most_similar(version, files)
       else:
           path = None

    if path is None:
        raise OSError('Index path does not exist: %s' % path_)

    return path


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


# ### Private protocol ########################################################

VERSION_RE = re.compile('index-([0-9.]+).json')

def _distance(version):
    def key(v):
        score = 0
        for i, (m, n) in enumerate(zip(v[-2::-1], version[-2::-1])):
            score += 10**i * abs(int(m)-int(n))
        if v[-1] != version[-1]:
            score += 0.5
        return score
    return key


def _get_current_version():
    version = '{}.{}.{}'.format(
        sys.version_info.major, sys.version_info.minor, sys.version_info.micro
    )
    return version


def _get_most_similar(version, names):
    if len(names) == 0:
        path = None

    elif len(names) == 1:
        path = names[0]

    else:
        versions = [_get_version(name) for name in names]
        v_min = min(versions, key=_distance(parse_version(version)))
        path = names[versions.index(v_min)]

    return path


def _get_version(path):
    v = VERSION_RE.search(basename(path))
    if v is None:
        raise RuntimeError('Invalid index name: Should be index-x.y.z.json')
    return parse_version(v.groups()[0])
