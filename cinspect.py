import inspect
import os
from os.path import expanduser

from index.reader import Reader
from _types import CInspectObject, PythonObject, get_cinspect_object

igetsource = inspect.getsource  # hack to allow patching in, inside IPython
igetfile = inspect.getfile

SOURCE_DIR = expanduser(os.getenv('PY_SOURCE_DIR', '~/software/random/cpython'))

def getfile(obj):
    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        path = igetfile(obj.obj)

    else:
        reader = Reader()
        path = reader.get_file(obj)

    return path

def getsource(obj):

    if not isinstance(obj, CInspectObject):
        obj = get_cinspect_object(obj)

    if isinstance(obj, PythonObject):
        source = igetsource(obj.obj)

    else:
        reader = Reader()
        source = reader.get_source(obj)

    return source
