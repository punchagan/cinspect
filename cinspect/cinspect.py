from __future__ import absolute_import, print_function

import inspect
import os
from os.path import expanduser

from .index.reader import Reader
from ._patch_helpers import inspect_restored
from ._types import CInspectObject, PythonObject, get_cinspect_object


SOURCE_DIR = expanduser(os.getenv('PY_SOURCE_DIR', '~/software/random/cpython'))


def getfile(obj):
    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        with inspect_restored():
            path = inspect.getfile(obj.obj)

    else:
        reader = Reader()
        path = reader.get_file(obj)

    return path


def getsource(obj):
    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        with inspect_restored():
            source = inspect.getsource(obj.obj)

    else:
        reader = Reader()
        source = reader.get_source(obj)

    return source
