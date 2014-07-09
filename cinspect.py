import os
from os.path import expanduser
import types

import inspect
from index import Index

igetsource = inspect.getsource  # hack to allow patching in, inside IPython
igetfile = inspect.getfile

SOURCE_DIR = expanduser(os.getenv('PY_SOURCE_DIR', '~/software/random/cpython'))

class InspectObject(object):
    """ A simple wrapper around the object we are trying to inspect. """

    def __init__(self, obj):
        self.obj = obj

    @property
    def module(self):
        return self.obj.__module__

    @property
    def name(self):
        return self.obj.__name__

    @property
    def type_name(self):
        return type(self.obj.__self__).__name__

    def get_hierarchy(self):
        hierarchy = {
            'module': self.module,
            'name' : self.name,
            'type_name' : self.type_name,
            'type': self.__class__.__name__
        }
        return hierarchy

class PythonObject(InspectObject):
    pass

class BuiltinFunction(InspectObject):
    @property
    def type_name(self):
        return None


class BuiltinMethod(InspectObject):
    @property
    def type_name(self):
        if isinstance(self.obj.__self__, type):
            type_name = self.obj.__self__.__name__

        else:
            type_name = super(BuiltinMethod, self).type_name

        return type_name

class MethodDescriptor(BuiltinMethod):
    @property
    def module(self):
        return None

    @property
    def type_name(self):
        return self.obj.__objclass__.__name__

class Module(InspectObject):
    @property
    def module(self):
        return None

    @property
    def type_name(self):
        return None

class Type(InspectObject):
    @property
    def type_name(self):
        return self.name

def get_inspect_object(obj):
    """ Returns the object wrapped in the appropriate InspectObject class. """

    try:
        igetsource(obj)
    except (TypeError, IOError) as e:
        # The code to deal with this case is below
        pass
    else:
        return PythonObject(obj)

    if inspect.isbuiltin(obj):
        if obj.__module__ is None:
            # fixme: we could possibly check in `types` to see if it's really a
            # built-in...
            return BuiltinMethod(obj)
        else:
            # Any builtin/compiled functions ...
            return BuiltinFunction(obj)

    elif inspect.ismethoddescriptor(obj):
        return MethodDescriptor(obj)

    elif inspect.ismodule(obj):
        return Module(obj)

    elif inspect.isclass(obj):
        return Type(obj)

    elif is_builtin_type_instance(obj):
        return Type(obj.__class__)

    else:
        raise NotImplementedError

def getfile(obj):
    if not isinstance(obj, InspectObject):
        obj = get_inspect_object(obj)

    if isinstance(obj, PythonObject):
        path = igetfile(obj.obj)

    else:
        index = Index()
        path = index.get_file(obj.get_hierarchy())

    return path

def getsource(obj):

    if not isinstance(obj, InspectObject):
        obj = get_inspect_object(obj)

    if isinstance(obj, PythonObject):
        source = igetsource(obj.obj)

    else:
        index = Index()
        source = index.get_source(obj.get_hierarchy())

    return source


def is_builtin_type_instance(obj):
    # fixme: is there a better way to do this?
    # fixme: there are missing builtins, here!
    return (
        isinstance(obj, types.DictType) or
        isinstance(obj, types.ListType) or
        isinstance(obj, set)
    )
