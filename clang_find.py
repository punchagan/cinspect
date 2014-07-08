# FIXME:

# - Clean up the API.  Too many functions thrown around.

# - Add some sort of caching.  The tests for inspection jumped up an ordere of
# magnitude, by shifting to using clang from regexes.

import clang.cindex


# fixme: what's going on here?
def get_kind(cursor):
    """ There are unknown cursor kinds! Why?! """
    try:
        return cursor.kind
    except ValueError:
        return None


def get_pymethod_def_mapping(cursor):
    """ Visits all PyMethodDef nodes and returns a unified mapping. """

    mapping = {}

    def visitor(cursor):
        if get_kind(cursor) == clang.cindex.CursorKind.VAR_DECL:
            children = list(cursor.get_children())

            if len(children) > 1 and children[0].displayname == 'PyMethodDef':
                if children[1].kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
                    for entry in python_object_from_cursor_by_kind(children[1]):
                        if entry is not None and len(entry) == 4:
                            py_name, c_name, _, _ = entry

                            if (isinstance(py_name, basestring) and
                                py_name.startswith('"') and
                                py_name.endswith('"')):

                                mapping[eval(py_name)] = c_name

        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return mapping


def get_type_object_mapping(cursor):
    """ Visits all PyTypeObject nodes and returns a mapping of name to cursors. """

    mapping = {}

    def visitor(cursor):
        if get_kind(cursor) == clang.cindex.CursorKind.VAR_DECL:
            children = list(cursor.get_children())

            if len(children) > 1 and children[0].displayname == 'PyTypeObject':
                parsed_definition = python_object_from_cursor_by_kind(children[1])
                if parsed_definition is not None and len(parsed_definition) >= 4:
                    name = parsed_definition[3]
                    if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
                        mapping[eval(name)] = cursor

        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return mapping


def get_code_for_function(cursor, name):
    """ Return the code for a function with the given name given a cursor.

    """

    def visitor(cursor, parent=None):
        if get_kind(cursor) == clang.cindex.CursorKind.FUNCTION_DECL:
            if cursor.spelling == name:
                return get_code_from_cursor(cursor)

        for child in cursor.get_children():
            code = visitor(child, cursor)
            if code is not None:
                return code

    return visitor(cursor)


def get_code_from_cursor(cursor):
    """ Return a string with the code, given a cursor object. """

    start, end = cursor.extent.begin_int_data, cursor.extent.end_int_data

    with open(cursor.location.file.name) as f:
        # fixme: I have no idea why we are being offset by 2.
        # Offset of 1, could be because the marker is after the first char,
        # another offset of 1 could be because the indexing starts from 1?
        f.read(start-2)
        text = f.read(end-start)

    return text

# fixme: this isn't really returning a python object for everything..
def python_object_from_cursor_by_kind(cursor):
    """ Return a Python object based on the kind of the cursor.

    Recursively, manipulates all the objects contained within.

    """

    cursor_kind = get_kind(cursor)

    if cursor_kind is None:
        obj = None

    elif cursor_kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
        obj = [
            python_object_from_cursor_by_kind(c) for c in cursor.get_children()
        ]

    elif cursor_kind == clang.cindex.CursorKind.CSTYLE_CAST_EXPR:
        obj = list(cursor.get_children())[-1].displayname

    elif cursor_kind == clang.cindex.CursorKind.UNEXPOSED_EXPR:
        children = list(cursor.get_children())
        if len(children) > 1:
            obj = [
                python_object_from_cursor_by_kind(c) for c in children
            ]

        elif len(children) == 1:
            obj = python_object_from_cursor_by_kind(children[0])

        else:
            obj = ''.join([t.spelling for t in cursor.get_tokens()])

    elif cursor_kind == clang.cindex.CursorKind.STRING_LITERAL:
        obj = cursor.get_tokens().next().spelling

    elif cursor_kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        tokens = list(cursor.get_tokens())
        if tokens:
            assert tokens[0].spelling == cursor.displayname
        obj = cursor.displayname
        # obj = cursor.get_tokens().next().spelling

    else:
        obj = None

    return obj


def get_cursor_for_file(path):
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

    if len(diagnostics) > 0:
        import pprint
        pprint.pprint(diagnostics)
        raise RuntimeError('There were parse errors')

    return tu


def get_code_from_file(path, py_name, object_type='file'):
    """ Return the C-code of a function given it's py_name, and a path. """

    tu = get_cursor_for_file(path)
    if object_type == 'file':
        mapping = get_pymethod_def_mapping(tu.cursor)
        code = get_code_for_function(tu.cursor, mapping[py_name])

    elif object_type == 'class':
        mapping = get_type_object_mapping(tu.cursor)
        # fixme: function -> class
        cursor = mapping.get(py_name, None)
        if cursor is not None:
            code = get_code_from_cursor(cursor)
        else:
            code = None

    elif object_type == 'module':
        with open(path) as f:
            code = f.read()

    return code


if __name__ == '__main__':
    import sys
    path, py_name = sys.argv[1:3]
    # print get_code_from_file(path, py_name)
    print get_code_from_file(path, 'dict', 'class')
