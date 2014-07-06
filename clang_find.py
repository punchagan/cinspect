import clang.cindex

def get_pymethod_def_mapping(cursor):
    """ Visits all PyMethodDef nodes and returns a unified mapping. """

    mapping = {}

    def py_method_def_visitor(cursor, parent=None):
        if cursor.is_definition() and cursor.kind == clang.cindex.CursorKind.VAR_DECL:
            children = list(cursor.get_children())
            if len(children) > 0 and children[0].displayname == 'PyMethodDef':
                children = list(cursor.get_children())
                assert len(children) == 2
                for child in children[1].get_children():
                    for kind in [clang.cindex.CursorKind.STRING_LITERAL, clang.cindex.CursorKind.DECL_REF_EXPR]:
                        foo = search_cursor_kind(child, kind)
                        # print [token.spelling for token in foo.get_tokens()], kind, 'xxxxxxx'
                        mapping[1] = foo
                        if foo is not None:
                            print foo.spelling, kind, len(list(foo.get_children()))
                            print [(c.spelling, c.kind) for c in foo.get_children()]

        for child in cursor.get_children():
            py_method_def_visitor(child, cursor)

    py_method_def_visitor(cursor)

    return mapping


def search_cursor_kind(cursor, kind):
    if cursor.kind == kind:
        return cursor
    else:
        for child in cursor.get_children():
            if search_cursor_kind(child, kind) is not None:
                return child




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
