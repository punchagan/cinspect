from __future__ import absolute_import, print_function

import inspect

from .index.reader import Reader
from ._patch_helpers import inspect_restored
from ._types import CInspectObject, PythonObject, get_cinspect_object


def getfile(obj, index_path=None):
    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        with inspect_restored():
            path = inspect.getfile(obj.obj)

    else:
        path = Reader(index_path).get_file(obj)

    return path


def getsource(obj, index_path=None):
    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        with inspect_restored():
            source = inspect.getsource(obj.obj)

    else:
        source = Reader(index_path).get_source(obj)

    return source
