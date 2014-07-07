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

    else:
        obj = None

    return obj


if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    extra_args = [
        '-v',
        '-I/usr/lib/clang/3.5/include',
        '-I/home/punchagan/software/random/cpython/Include',
        '-I/home/punchagan/software/random/cpython/'
    ]

    index = clang.cindex.Index.create()
    tu = index.parse(path, args=extra_args)

    diagnostics = list(tu.diagnostics)
    if len(diagnostics) > 0:
        print 'There were parse errors'
        import pprint
        pprint.pprint(diagnostics)
    else:
        c = get_pymethod_def_mapping(tu.cursor)
        print c
