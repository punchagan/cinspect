from __future__ import absolute_import, print_function

import sys
if sys.version_info.major > 2:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
import os


def spin(every, state=['|', 0]):
    if state[1] >= every:
        state[1] = 0
    if state[1] == 0:
        sigils = '|\-/'
        state[0] = sigils[(sigils.index(state[0])+1) % 4]
        sys.stderr.write('\r'+state[0])
        sys.stderr.flush()
    state[1] += 1

reporthook = lambda x, y, z: spin(5)

dest = os.path.expanduser('~/.index.json')
urlretrieve('http://ballingt.com/assets/.index.json', dest, reporthook)
