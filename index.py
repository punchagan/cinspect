#!/usr/bin/env python
""" A module to index the C-sources of a library.

Usage: index.py /path/to/library

The library looks up the C files in the library and indexes them, so that
cinspect can use those indexes obtain the source code.

The indexes actually save the full (required) source, and not references of the
extent of the definition.  The source files can be removed, once indexed.

The indexer saves a hash (md5?) of the files, so that the indexing can be run
any number of times to detect any changes in the file, and re-index them.

"""

# Standard library
from hashlib import md5
import json
from os.path import (
    abspath, exists, expanduser, isdir, join, splitext, walk
)

# Local library.
from clang_find import get_cursor_for_file, indexing_visitor
from _types import Module, Type


class Index(object):
    """ An object to create and read C-source indexes for packages. """

    #### 'Object' protocol ####################################################

    def __init__(self, db=None):
        if db is None:
            db = '.index.json'
        self.db = abspath(db)

    #### 'Index' protocol #####################################################

    def get_source(self, obj):
        """ Return the source for the object."""

        data = self._get_data(obj)
        return data['source']

    def get_file(self, obj):
        """ Return the file where the object has been defined. """

        data = self._get_data(obj)
        return data['path']

    def index(self, path):
        """ Create the indexes for sources at a given path.

        NOTE: Indexing is not thread-safe, right now!

        """

        if not exists(path):
            raise OSError('Path %s does not exist' % path)

        if isdir(path):
            self._update_dir_in_index(path)

        else:
            data = self._read_index()
            self._update_file_in_index(path, data)
            self._write_index(data)

    #### 'Private' protocol ###################################################

    def _index_files_in_dir(self, data, dirname, fnames):
        """ The function we pass on to the directory tree walk function. """

        # fixme: additional argument to ignore files?
        for fname in sorted(fnames):
            if is_c_file(fname):
                path = join(dirname, fname)
                self._update_file_in_index(path, data)

    def _get_data(self, obj):
        """ Get the data for the given object. """

        if not exists(self.db):
            raise OSError('Index data not found at %s' % self.db)

        indexed_data = self._read_index()

        name = obj.name
        type_name = obj.type_name
        module = obj.module

        if isinstance(obj, Type):
            objects = indexed_data.get('objects', {})
            data = objects.get(name, '')

        elif isinstance(obj, Module):
            objects = indexed_data.get('modules', {})
            data = objects.get(name, '')

        else:
            method_names = indexed_data.get('method_names', {})
            # fixme: Use the information from the module/object on which
            # mapping to look in!
            for _, group in method_names.iteritems():
                if name in group:
                    if type_name is not None and not group[name].startswith(type_name):
                        continue
                    elif module is not None and not group[name].startswith(module.strip('_')):
                        continue
                    method_name = group[name]
                    data = indexed_data.get('methods', {}).get(method_name, '')
                    break

            else:
                data = {'source': '', 'path': ''}

        return data

    def _get_file_indexes(self, path, data):
        """ Index the sources for all the objects and methods. """

        try:
            tu = get_cursor_for_file(path)

        except:
            # fixme: need a verbosity setting.
            print 'Could not parse %s' % path
            data = {}

        else:
            indexing_visitor(tu.cursor, data, path)

    def _read_index(self):
        """ Read the index and return the data.

        Returns an empty dictionary if no index exists.

        """

        if exists(self.db):
            with open(self.db) as f:
                data = json.load(f)
        else:
            data = {}

        return data

    def _tag_with_file_path(self, data, path):
        """ Given a dictionary with names mapped to sources, we also add path.

        """

        mapping = {}

        for key, value in data.iteritems():
            if isinstance(value, basestring):
                mapping[key] = {'source': value, 'path': path}
            else:
                mapping[key] = self._tag_with_file_path(value, path)

        return mapping

    def _update_dir_in_index(self, path):
        """ Walks through the directory, and indexes all the files in it. """

        data = self._read_index()
        walk(expanduser(path), self._index_files_in_dir, data)
        self._write_index(data)

    def _update_file_in_index(self, path, data):
        hashes = data.setdefault('hashes', {})
        current_hash = get_file_hash(path)
        if path not in hashes or current_hash != hashes[path]:
            self._get_file_indexes(path, data)
            hashes[path] = current_hash

    def _write_index(self, data):
        """ Read the index and return the data. """

        with open(self.db, 'w') as f:
            json.dump(data, f, indent=2)


def get_file_hash(path):
    """ Return the hash of a file. """

    with open(path) as f:
        h = md5(f.read())

    return h.hexdigest()

def is_c_file(path):
    return splitext(path)[-1].lower() == '.c'


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        paths = sys.argv[1:]

    else:
        paths = ['~/software/random/cpython']

    index = Index()
    for path in paths:
        index.index(expanduser(path))
