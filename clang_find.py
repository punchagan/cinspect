# FIXME:

# - Clean up the API.  Too many functions thrown around.

# - Add some sort of caching.  The tests for inspection jumped up an ordere of
# magnitude, by shifting to using clang from regexes.

import clang.cindex


def is_py_method_def(cursor):
    if cursor.kind != clang.cindex.CursorKind.VAR_DECL:
        return False

    children = list(cursor.get_children())

    if len(children) > 1 and children[0].displayname == 'PyMethodDef':
        if children[1].kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
            return True

    return False


def parse_py_method_def(cursor):
    value = list(cursor.get_children())[1]
    method_map = {}

    for entry in python_object_from_cursor_by_kind(value):
        if entry is not None and len(entry) == 4:
            py_name, c_name, _, _ = entry

            if (isinstance(py_name, basestring) and
                py_name.startswith('"') and
                py_name.endswith('"')):

                method_map[py_name[1:-1]] = c_name

    return method_map


def get_pymethod_def_mapping(cursor):
    """ Visits all PyMethodDef nodes and returns a unified mapping. """

    maps = {}

    def visitor(cursor):
        if is_py_method_def(cursor):
            maps.setdefault(cursor.displayname, {}).update(
                parse_py_method_def(cursor)
            )

        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return maps

def is_py_type_object(cursor):
    if cursor.kind != clang.cindex.CursorKind.VAR_DECL:
        return False

    children = list(cursor.get_children())
    if len(children) > 1 and children[0].displayname == 'PyTypeObject':
        return True

    return False


def parse_py_type_object(cursor):
    children = list(cursor.get_children())
    parsed_definition = python_object_from_cursor_by_kind(children[1])
    if parsed_definition is not None and len(parsed_definition) >= 4:
        name = parsed_definition[3]
        if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
            return name[1:-1], get_code_from_cursor(cursor)

    return None, None


def get_type_object_mapping(cursor):
    """ Visits all PyTypeObject nodes and returns a mapping of name to cursors. """

    mapping = {}

    def visitor(cursor):
        if is_py_type_object(cursor):
            name, code = parse_py_type_object(cursor)
            if name is not None:
                mapping[name] = code
        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return mapping


def is_function(cursor):
    return cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL

def parse_function(cursor):
    return {cursor.spelling: get_code_from_cursor(cursor)}

def get_method_mapping(cursor):
    """ Visit all function definitions and returns a mapping of name -> source. """

    method_map = {}

    def visitor(cursor):
        if is_function(cursor):
            method_map.update(parse_function(cursor))

        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return method_map

def is_py_init_module(cursor):
    if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
        if cursor.displayname.startswith('Py_InitModule'):
            return True

    return False

def parse_py_init_module(cursor):
    name_cursor = list(cursor.get_children())[1]
    tokens = list(name_cursor.get_tokens())
    if len(tokens) > 0:
        name = tokens[0].spelling
        if isinstance(name, basestring) and name.startswith('"') and name.endswith('"'):
            return {name[1:-1]: get_code_from_cursor(cursor.translation_unit.cursor)}

    return {}



def get_module_mapping(cursor):
    """ Returns a mapping from the name to the source, if a module is defined. """

    modules = {}

    def visitor(cursor):
        if is_py_init_module(cursor):
            modules.update(parse_py_init_module(cursor))
        for child in cursor.get_children():
            visitor(child)

    visitor(cursor)

    return modules


def get_code_from_cursor(cursor):
    """ Return a string with the code, given a cursor object. """

    start, end = cursor.extent.begin_int_data, cursor.extent.end_int_data

    file = cursor.location.file
    path = file.name if file is not None else cursor.translation_unit.spelling

    with open(path) as f:
        # fixme: I have no idea why we are being offset by 2.
        # Offset of 1, could be because the marker is after the first char,
        # another offset of 1 could be because the indexing starts from 1?
        f.read(start-2)
        text = make_unicode(f.read(end-start))

    return text

# fixme: this isn't really returning a python object for everything..
def python_object_from_cursor_by_kind(cursor):
    """ Return a Python object based on the kind of the cursor.

    Recursively, manipulates all the objects contained within.

    """

    if cursor.kind is None:
        obj = None

    elif cursor.kind == clang.cindex.CursorKind.INIT_LIST_EXPR:
        obj = [
            python_object_from_cursor_by_kind(c) for c in cursor.get_children()
        ]

    elif cursor.kind == clang.cindex.CursorKind.CSTYLE_CAST_EXPR:
        obj = list(cursor.get_children())[-1].displayname

    elif cursor.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR:
        children = list(cursor.get_children())
        if len(children) > 1:
            obj = [
                python_object_from_cursor_by_kind(c) for c in children
            ]

        elif len(children) == 1:
            obj = python_object_from_cursor_by_kind(children[0])

        else:
            obj = ''.join([t.spelling for t in cursor.get_tokens()])

    elif cursor.kind == clang.cindex.CursorKind.STRING_LITERAL:
        obj = cursor.get_tokens().next().spelling

    elif cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
        obj = cursor.displayname

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

    # fixme: we need to actually see what serverity level is bad ...
    if len(diagnostics) > 0:
        import pprint
        # fixme: we need some kind of verbosity level.
        pprint.pprint(diagnostics)
        raise RuntimeError('There were parse errors')

    return tu


def make_unicode(text):
    try:
        text = text.decode('utf8')
    except UnicodeDecodeError:
        text = text.decode('iso-8859-15')

    return text


if __name__ == '__main__':
    import sys
    path = sys.argv[1]

    tu = get_cursor_for_file(path)
    print get_pymethod_def_mapping(tu.cursor).keys()
    print get_type_object_mapping(tu.cursor).keys()
    print get_method_mapping(tu.cursor).keys()
    print get_module_mapping(tu.cursor).keys()
