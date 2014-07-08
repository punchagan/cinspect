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
from clang_find import (
    get_cursor_for_file, get_pymethod_def_mapping, get_type_object_mapping,
    get_code_from_cursor, get_method_mapping, get_module_mapping
)


class Index(object):

    def __init__(self, db=None):
        if db is None:
            db = '.index.json'
        db = abspath(db)
        self.db = db

    def get_source_from_hierarchy(self, hierarchy):
        if not exists(self.db):
            raise OSError('Index data not found at %s' % self.db)

        data = self._read_index()

        name = hierarchy.get('name')
        module = hierarchy.get('module')
        type_name = hierarchy.get('type_name')
        type_ = hierarchy.get('type')


        if type_ == 'Type':
            objects = data.get('objects', {})
            code = objects.get(name, '')

        elif type_ == 'Module':
            objects = data.get('modules', {})
            code = objects.get(name, '')

        else:
            method_names = data.get('method_names', {})
            for _, group in method_names.iteritems():
                if name in group:
                    if type_name is not None and not group[name].startswith(type_name):
                        continue
                    method_name = group[name]
                    code = data.get('methods', {}).get(method_name, '')
                    break

            else:
                code = ''

        return code

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

    def _update_dir_in_index(self, path):
        """ Walks through the directory, and indexes all the files in it. """

        data = self._read_index()
        walk(expanduser(path), self._index_files_in_dir, data)
        self._write_index(data)


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

    def _write_index(self, data):
        """ Read the index and return the data. """

        with open(self.db, 'w') as f:
            json.dump(data, f, indent=2)

    def _index_files_in_dir(self, data, dirname, fnames):
        # fixme: ignore files?
        # testsuites by default. (if test in root name...)?
        for fname in sorted(fnames):
            if is_c_file(fname):
                path = join(dirname, fname)
                self._update_file_in_index(path, data)

    def _update_file_in_index(self, path, data):
        hashes = data.setdefault('hashes', {})
        current_hash = get_file_hash(path)
        if path not in hashes or current_hash != hashes[path]:
            objects, method_names, methods, modules = self._get_file_indexes(path)

            # fixme: this should be by module.
            data.setdefault('objects', {}).update(objects)
            data.setdefault('method_names', {}).update(method_names)
            data.setdefault('methods', {}).update(methods)
            data.setdefault('modules', {}).update(modules)
            hashes[path] = current_hash

    def _get_file_indexes(self, path):
        """ Index the sources for all the objects and methods. """

        try:
            tu = get_cursor_for_file(path)

        except:
            # fixme: need a verbosity setting.
            print 'Could not parse %s' % path
            objects = {}
            method_names = {}
            methods = {}
            modules = {}

        else:
            objects = get_type_object_mapping(tu.cursor)
            method_names = get_pymethod_def_mapping(tu.cursor)
            methods = get_method_mapping(tu.cursor)
            modules = get_module_mapping(tu.cursor)

        return objects, method_names, methods, modules


def is_c_file(path):
    return splitext(path)[-1].lower() == '.c'


def get_file_hash(path):
    """ Return the hash of a file. """

    with open(path) as f:
        h = md5(f.read())

    return h.hexdigest()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        paths = sys.argv[1:]

    else:
        paths = ['~/software/random/cpython']

    index = Index()
    for path in paths:
        index.index(expanduser(path))
