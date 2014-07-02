import inspect

from cinspect import getsource, getfile

import IPython.core.oinspect as OI
from IPython.utils.py3compat import cast_unicode

old_find_file = OI.find_file
old_getsource = inspect.getsource

inspect.getsource = getsource

def patch_find_file(obj):
    fname = old_find_file(obj)
    if fname is None:
        try:
            fname = cast_unicode(getfile(obj))
        except:
            pass
    return fname

OI.find_file = patch_find_file
