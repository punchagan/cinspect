from __future__ import absolute_import, print_function

import glob
from os.path import dirname
import subprocess

import cinspect.vendor.clang.cindex as CI


def can_find_clang_headers(clang_args):
    flags = 0
    currentFile = ("test.c", '#include "limits.h"\n#include "stddef.h"\n')
    try:
        index = CI.Index.create()
        tu = index.parse("test.c", clang_args, [currentFile], flags)
    except CI.TranslationUnitLoadError, e:
        return False
    return len(tu.diagnostics) == 0


def get_libclang_headers():
    try:
        paths = _ask_clang()
    except OSError:
        paths = _guess_paths()

    return ['-I%s' % path for path in paths]


def _ask_clang():
    command = ['clang', '-xc++', '-E', '-v', '/dev/null']
    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    start_str, end_str = 'search starts here:\n', '\nEnd of search list.'
    start = output.rindex(start_str) + len(start_str)
    end = output.index(end_str)
    return output[start:end].split()


def _guess_paths(library_path=None):
    """Tries to look for clang headers in known paths.

    This code is very similar to the code in
    https://github.com/Rip-Rip/clang_complete/blob/master/plugin/libclang.py
    """

    if library_path is None:
        library_path = (
            CI.Config.library_path or
            (CI.Config.library_file and dirname(CI.Config.library_file))
        )

    if library_path is None:
        raise RuntimeError(
            'No library path set, try setting '
            'clang.cindex.Config.set_library_path'
        )

    known_paths = [
        library_path + '/../lib/clang',  # default value
        library_path + '/../clang',      # gentoo
        library_path + '/clang',         # opensuse
        library_path + '/',              # Google
        '/usr/lib64/clang',              # x86_64 (openSUSE, Fedora)
        '/usr/lib/clang'
    ]

    for path in known_paths:
        for pattern in ('/include', '/*/include'):
            for include_dir in glob.glob(path + pattern):
                clang_args = ['-I%s' % include_dir]
                if can_find_clang_headers(clang_args):
                    return [include_dir]
    return []


if __name__ == '__main__':
    CI.Config.set_library_file('/usr/lib/x86_64-linux-gnu/libclang.so.1')
    print(get_libclang_headers())
