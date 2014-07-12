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
from os.path import (
    abspath, exists, expanduser, isdir, join, splitext, walk
)

# Local library
from serialize import read_index, write_index

# 3rd party library.
import cinspect.vendor.clang.cindex as ci


class Writer(object):
    """ An object to create C-source indexes for packages. """

    #### 'Object' protocol ####################################################

    def __init__(self, db=None):
        if db is None:
            # fixme: this path is hardcoded at two places, reader and writer.
            db = expanduser('~/.index.json')
        self.db = abspath(db)

    #### 'Writer' protocol ####################################################

    def create(self, path):
        """ Create the indexes for sources at a given path.

        NOTE: Indexing is not thread-safe, right now!

        """

        if not exists(path):
            raise OSError('Path %s does not exist' % path)

        if isdir(path):
            self._update_dir_in_index(path)

        else:
            data = read_index(self.db)
            self._update_file_in_index(path, data)
            write_index(self.db, data)

    #### 'Private' protocol ###################################################

    def _get_code_from_cursor(self, cursor):
        """ Return a string with the code, given a cursor object. """

        start, end = cursor.extent.begin_int_data, cursor.extent.end_int_data

        file = cursor.location.file
        path = file.name if file is not None else cursor.translation_unit.spelling

        with open(path) as f:
            # fixme: I have no idea why we are being offset by 2.
            # Offset of 1, could be because the marker is after the first char,
            # another offset of 1 could be because the indexing starts from 1?
            f.read(start-2)
            text = self._make_unicode(f.read(end-start))

        return text

    def _get_cursor_for_file(self, path):
        """ Returns a cursor object, given the path to a file.

        Raises a RuntimeError if the file couldn't be parsed, without errors.

        """

        # fixme: my specific paths.
        extra_args = [
            '-I/usr/lib/clang/3.5/include',
            '-I/home/punchagan/software/random/cpython/Include',
            '-I/home/punchagan/software/random/cpython/'
        ]

        index = ci.Index.create()
        tu = index.parse(path, args=extra_args)
        diagnostics = list(tu.diagnostics)

        # fixme: we need to actually see what serverity level is bad ...
        if len(diagnostics) > 0:
            import pprint
            # fixme: we need some kind of verbosity level.
            pprint.pprint(diagnostics)
            raise RuntimeError('There were parse errors')

        return tu

    def _get_file_hash(self, path):
        """ Return the hash of a file. """

        with open(path) as f:
            h = md5(f.read())

        return h.hexdigest()

    def _index_file(self, path, data):
        """ Index the sources for all the objects and methods. """

        tu = self._get_cursor_for_file(path)
        self._indexing_visitor(tu.cursor, data, path)

    def _index_files_in_dir(self, data, dirname, fnames):
        """ The function we pass on to the directory tree walk function. """

        # fixme: additional argument to ignore files?
        for fname in sorted(fnames):
            if self._is_c_file(fname):
                path = join(dirname, fname)
                self._update_file_in_index(path, data)

    def _indexing_visitor(self, cursor, data, path):
        """ Visits all nodes and returns a mapping of various kinds of definitions.

        """

        objects = data.setdefault('objects', {})
        method_names = data.setdefault('method_names', {})
        methods = data.setdefault('methods', {})
        modules = data.setdefault('modules', {})


        if self._is_function(cursor):
            methods.update(
                self._tag_with_file_path(self._parse_function(cursor), path)
            )

        elif self._is_py_method_def(cursor):
            method_names.update(self._parse_py_method_def(cursor))

        elif self._is_py_type_object(cursor):
            objects.update(
                self._tag_with_file_path(self._parse_py_type_object(cursor), path)
            )

        elif self._is_py_init_module(cursor):
            modules.update(
                self._tag_with_file_path(self._parse_py_init_module(cursor), path)
            )

        else:
            # We don't care about any other types of nodes (yet)
            pass

        for child in cursor.get_children():
            self._indexing_visitor(child, data, path)

    def _is_c_file(self, path):
        return splitext(path)[-1].lower() == '.c'

    def _is_function(self, cursor):
        return cursor.kind == ci.CursorKind.FUNCTION_DECL

    def _is_py_init_module(self, cursor):
        if cursor.kind == ci.CursorKind.CALL_EXPR:
            if cursor.displayname.startswith('Py_InitModule'):
                return True

        return False

    def _is_py_method_def(self, cursor):
        if cursor.kind != ci.CursorKind.VAR_DECL:
            return False

        children = list(cursor.get_children())

        if len(children) > 1 and children[0].displayname == 'PyMethodDef':
            if children[1].kind == ci.CursorKind.INIT_LIST_EXPR:
                return True

        return False

    def _is_py_type_object(self, cursor):
        if cursor.kind != ci.CursorKind.VAR_DECL:
            return False

        children = list(cursor.get_children())
        if len(children) > 1 and children[0].displayname == 'PyTypeObject':
            return True

        return False

    def _make_unicode(self, text):

        for encoding in ('utf8', 'iso-8859-15'):
            try:
                return text.decode(encoding)
            except UnicodeDecodeError:
                pass

        return text.decode('utf8', 'replace')

    def _parse_function(self, cursor):
        return {cursor.spelling: self._get_code_from_cursor(cursor)}

    def _parse_py_init_module(self, cursor):
        name_cursor = list(cursor.get_children())[1]
        tokens = list(name_cursor.get_tokens())
        if len(tokens) > 0:
            name = tokens[0].spelling
            if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
                return {name[1:-1]: self._get_code_from_cursor(cursor.translation_unit.cursor)}

        return {}

    def _parse_py_method_def(self, cursor):
        value = list(cursor.get_children())[1]
        method_map = {}

        for entry in self._python_object_from_cursor_by_kind(value):
            if entry is not None and len(entry) == 4:
                py_name, c_name, _, _ = entry

                if (isinstance(py_name, basestring) and
                    py_name.startswith('"') and
                    py_name.endswith('"')):

                    method_map[py_name[1:-1]] = c_name

        return {cursor.displayname: method_map}

    def _parse_py_type_object(self, cursor):
        children = list(cursor.get_children())
        parsed_definition = self._python_object_from_cursor_by_kind(children[1])
        if parsed_definition is not None and len(parsed_definition) >= 4:
            name = parsed_definition[3]
            if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
                return {name[1:-1]: self._get_code_from_cursor(cursor)}

        return {}

    # fixme: this isn't really returning a python object for everything..
    def _python_object_from_cursor_by_kind(self, cursor):
        """ Return a Python object based on the kind of the cursor.

        Recursively, manipulates all the objects contained within.

        """

        if cursor.kind is None:
            obj = None

        elif cursor.kind == ci.CursorKind.INIT_LIST_EXPR:
            obj = [
                self._python_object_from_cursor_by_kind(c) for c in cursor.get_children()
            ]

        elif cursor.kind == ci.CursorKind.CSTYLE_CAST_EXPR:
            obj = list(cursor.get_children())[-1].displayname

        elif cursor.kind == ci.CursorKind.UNEXPOSED_EXPR:
            children = list(cursor.get_children())
            if len(children) > 1:
                obj = [
                    self._python_object_from_cursor_by_kind(c) for c in children
                ]

            elif len(children) == 1:
                obj = self._python_object_from_cursor_by_kind(children[0])

            else:
                obj = ''.join([t.spelling for t in cursor.get_tokens()])

        elif cursor.kind == ci.CursorKind.STRING_LITERAL:
            obj = cursor.get_tokens().next().spelling

        elif cursor.kind == ci.CursorKind.DECL_REF_EXPR:
            obj = cursor.displayname

        else:
            obj = None

        return obj


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

        data = read_index(self.db)
        walk(expanduser(path), self._index_files_in_dir, data)
        write_index(self.db, data)

    def _update_file_in_index(self, path, data):
        hashes = data.setdefault('hashes', {})
        current_hash = self._get_file_hash(path)
        if path not in hashes or current_hash != hashes[path]:
            try:
               self._index_file(path, data)
            except RuntimeError:
                # fixme: need a verbosity setting.
                print 'Could not parse %s' % path
            else:
                hashes[path] = current_hash

def main():
    import sys

    if len(sys.argv) > 1:
        paths = sys.argv[1:]

    else:
        paths = ['~/software/random/cpython']

    writer = Writer()
    for path in paths:
        writer.create(expanduser(path))


if __name__ == '__main__':
    main()
