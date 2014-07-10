# FIXME:
# - Clean up the API.  Too many functions thrown around.

import clang.cindex


def index_file(path, data):
    """ Index the sources for all the objects and methods. """

    try:
        tu = _get_cursor_for_file(path)

    except RuntimeError:
        # fixme: need a verbosity setting.
        print 'Could not parse %s' % path

    else:
        _indexing_visitor(tu.cursor, data, path)


#### 'Private' functions ######################################################


def _indexing_visitor(cursor, data, path):
    """ Visits all nodes and returns a mapping of various kinds of definitions.

    """

    objects = data.setdefault('objects', {})
    method_names = data.setdefault('method_names', {})
    methods = data.setdefault('methods', {})
    modules = data.setdefault('modules', {})

    def visitor(cursor):
        if _is_function(cursor):
            methods.update(
                _tag_with_file_path(_parse_function(cursor), path)
            )

        elif _is_py_method_def(cursor):
            method_names.update(_parse_py_method_def(cursor))

        elif _is_py_type_object(cursor):
            objects.update(
                _tag_with_file_path(_parse_py_type_object(cursor), path)
            )

        elif _is_py_init_module(cursor):
            modules.update(
                _tag_with_file_path(_parse_py_init_module(cursor), path)
            )

        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)


def _is_function(cursor):
    return cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL


def _parse_function(cursor):
    return {cursor.spelling: _get_code_from_cursor(cursor)}


def _is_py_method_def(cursor):
    if cursor.kind != clang.cindex.CursorKind.VAR_DECL:
        return False

    children = list(cursor.get_children())

    if len(children) > 1 and children[0].displayname == 'PyMethodDef':
        if children[1].kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
            return True

    return False


def _parse_py_method_def(cursor):
    value = list(cursor.get_children())[1]
    method_map = {}

    for entry in _python_object_from_cursor_by_kind(value):
        if entry is not None and len(entry) == 4:
            py_name, c_name, _, _ = entry

            if (isinstance(py_name, basestring) and
                py_name.startswith('"') and
                py_name.endswith('"')):

                method_map[py_name[1:-1]] = c_name

    return {cursor.displayname: method_map}

def _is_py_type_object(cursor):
    if cursor.kind != clang.cindex.CursorKind.VAR_DECL:
        return False

    children = list(cursor.get_children())
    if len(children) > 1 and children[0].displayname == 'PyTypeObject':
        return True

    return False


def _parse_py_type_object(cursor):
    children = list(cursor.get_children())
    parsed_definition = _python_object_from_cursor_by_kind(children[1])
    if parsed_definition is not None and len(parsed_definition) >= 4:
        name = parsed_definition[3]
        if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
            return {name[1:-1]: _get_code_from_cursor(cursor)}

    return {}


def _is_py_init_module(cursor):
    if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
        if cursor.displayname.startswith('Py_InitModule'):
            return True

    return False


def _parse_py_init_module(cursor):
    name_cursor = list(cursor.get_children())[1]
    tokens = list(name_cursor.get_tokens())
    if len(tokens) > 0:
        name = tokens[0].spelling
        if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
            return {name[1:-1]: _get_code_from_cursor(cursor.translation_unit.cursor)}

    return {}


def _tag_with_file_path(data, path):
    """ Given a dictionary with names mapped to sources, we also add path.

    """

    mapping = {}

    for key, value in data.iteritems():
        if isinstance(value, basestring):
            mapping[key] = {'source': value, 'path': path}
        else:
            mapping[key] = _tag_with_file_path(value, path)

    return mapping


def _get_code_from_cursor(cursor):
    """ Return a string with the code, given a cursor object. """

    start, end = cursor.extent.begin_int_data, cursor.extent.end_int_data

    file = cursor.location.file
    path = file.name if file is not None else cursor.translation_unit.spelling

    with open(path) as f:
        # fixme: I have no idea why we are being offset by 2.
        # Offset of 1, could be because the marker is after the first char,
        # another offset of 1 could be because the indexing starts from 1?
        f.read(start-2)
        text = _make_unicode(f.read(end-start))

    return text


# fixme: this isn't really returning a python object for everything..
def _python_object_from_cursor_by_kind(cursor):
    """ Return a Python object based on the kind of the cursor.

    Recursively, manipulates all the objects contained within.

    """

    if cursor.kind is None:
        obj = None

    elif cursor.kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
        obj = [
            _python_object_from_cursor_by_kind(c) for c in cursor.get_children()
        ]

    elif cursor.kind == clang.cindex.CursorKind.CSTYLE_CAST_EXPR:
        obj = list(cursor.get_children())[-1].displayname

    elif cursor.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR:
        children = list(cursor.get_children())
        if len(children) > 1:
            obj = [
                _python_object_from_cursor_by_kind(c) for c in children
            ]

        elif len(children) == 1:
            obj = _python_object_from_cursor_by_kind(children[0])

        else:
            obj = ''.join([t.spelling for t in cursor.get_tokens()])

    elif cursor.kind == clang.cindex.CursorKind.STRING_LITERAL:
        obj = cursor.get_tokens().next().spelling

    elif cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        obj = cursor.displayname

    else:
        obj = None

    return obj


def _get_cursor_for_file(path):
    """ Returns a cursor object, given the path to a file.

    Raises a RuntimeError if the file couldn't be parsed, without errors.

    """

    # fixme: my specific paths.
    extra_args = [
        '-I/usr/lib/clang/3.5/include',
        '-I/home/punchagan/software/random/cpython/Include',
        '-I/home/punchagan/software/random/cpython/'
    ]

    index = clang.cindex.Index.create()
    tu = index.parse(path, args=extra_args)
    diagnostics = list(tu.diagnostics)

    # fixme: we need to actually see what serverity level is bad ...
    if len(diagnostics) > 0:
        import pprint
        # fixme: we need some kind of verbosity level.
        pprint.pprint(diagnostics)
        raise RuntimeError('There were parse errors')

    return tu


def _make_unicode(text):

    for encoding in ('utf8', 'iso-8859-15'):
        try:
            return text.decode(encoding)
        except UnicodeDecodeError:
            pass

    return text.decode('utf8', 'replace')


if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    data = {}
    index_file(path, data)
    print data.keys()
