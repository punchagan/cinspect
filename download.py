import urllib
import os
import sys
f = urllib.urlopen('http://ballingt.com/assets/.index.json')
dest = open(os.path.expanduser('~/.index.json'), 'w')

def spin(every, state=['|', 0]):
    if state[1] >= every:
        state[1] = 0
    if state[1] == 0:
        sigils = '|\-/'
        state[0] = sigils[(sigils.index(state[0])+1) % 4]
        sys.stderr.write('\r'+state[0])
        sys.stderr.flush()
    state[1] += 1

for line in f:
    spin(400)
    dest.write(line)
