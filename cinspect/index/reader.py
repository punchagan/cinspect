#!/usr/bin/env python
""" A class to read indexes and get source of specific objects. """

from __future__ import absolute_import, print_function

# Standard library
from hashlib import md5
from os.path import (
    abspath, exists, expanduser, isdir, join, splitext, walk
)

# Local library.
from .._types import Module, Type
from .serialize import read_index


class Reader(object):
    """ A class to read indexes and get source of specific objects. """

    #### 'Object' protocol ####################################################

    def __init__(self, db=None):
        if db is None:
            db = expanduser('~/.index.json')
        self.db = abspath(db)

    #### 'Reader' protocol ####################################################

    def get_source(self, obj):
        """ Return the source for the object."""

        data = self._get_data(obj)
        return data['source']

    def get_file(self, obj):
        """ Return the file where the object has been defined. """

        data = self._get_data(obj)
        return data['path']

    #### 'Private' protocol ###################################################

    def _get_data(self, obj):
        """ Get the data for the given object. """

        if not exists(self.db):
            raise OSError('Index data not found at %s' % self.db)

        indexed_data = read_index(self.db)

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
