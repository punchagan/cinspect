from contextlib import contextmanager
import inspect

_igetsource = inspect.getsource
_igetfile = inspect.getfile


@contextmanager
def inspect_restored():
    igetsource = inspect.getsource
    igetfile = inspect.getfile
    inspect.getsource = _igetsource
    inspect.getfile = _igetfile
    try:
        yield
    finally:
        inspect.getsource = igetsource
        inspect.getfile = igetfile
