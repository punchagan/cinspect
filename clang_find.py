# FIXME:

# - Clean up the API.  Too many functions thrown around.

# - Add some sort of caching.  The tests for inspection jumped up an ordere of
# magnitude, by shifting to using clang from regexes.

import clang.cindex

def get_pymethod_def_mapping(cursor):
    """ Visits all PyMethodDef nodes and returns a unified mapping. """

    mapping = {}

    def py_method_def_visitor(cursor, parent=None):
        if cursor.kind == clang.cindex.CursorKind.VAR_DECL:
            children = list(cursor.get_children())

            if len(children) > 0 and children[0].displayname == 'PyMethodDef':
                assert len(children) == 2

                for entry in python_object_from_cursor_by_kind(children[1]):
                    if len(entry) == 4:
                        py_name, c_name, _, _ = entry
                        mapping[eval(py_name)] = c_name

        for child in cursor.get_children():
            py_method_def_visitor(child, cursor)

    py_method_def_visitor(cursor)

    return mapping


def get_code_for_function(cursor, name):
    """ Return the code for a function with the given name given a cursor.

    """

    def visitor(cursor, parent=None):
        if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
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

    if cursor.kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
        obj = [
            python_object_from_cursor_by_kind(c) for c in cursor.get_children()
        ]

    elif cursor.kind == clang.cindex.CursorKind.CSTYLE_CAST_EXPR:
        obj = list(cursor.get_children())[-1].displayname

    elif cursor.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR:
        children = list(cursor.get_children())
        assert len(children) == 1
        obj = python_object_from_cursor_by_kind(children[0])

    elif cursor.kind == clang.cindex.CursorKind.STRING_LITERAL:
        obj = cursor.get_tokens().next().spelling

    elif cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        obj = cursor.get_tokens().next().spelling

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


def get_code_from_file(path, py_name):
    """ Return the C-code of a function given it's py_name, and a path. """

    tu = get_cursor_for_file(path)
    if py_name is not None:
        mapping = get_pymethod_def_mapping(tu.cursor)
        code = get_code_for_function(tu.cursor, mapping[py_name])
    else:
        # fixme: this needs to be cleaned up when we add support for objects!
        with open(path) as f:
            code = f.read()

    return code


if __name__ == '__main__':
    import sys
    path, py_name = sys.argv[1:3]
    print get_code_from_file(path, py_name)
