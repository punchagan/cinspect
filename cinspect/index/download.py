from __future__ import absolute_import, print_function

import os
import shutil
import sys
import tempfile
import tarfile
if sys.version_info.major > 2:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve

ARCHIVE_URL = 'https://github.com/punchagan/cinspect-data/archive/master.tar.gz'


def copy_indexes(archive):
    extract_dir = os.path.dirname(archive)
    src_dir = os.path.join(extract_dir, 'cinspect-data-master')
    dst_dir = os.path.expanduser('~/.cinspect')

    with tarfile.open(archive, 'r:gz') as tf:
        tf.extractall(extract_dir)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    for name in os.listdir(src_dir):
        if name.endswith('.json'):
            src = os.path.join(src_dir, name)
            dst = os.path.join(dst_dir, name)
            copy = True
            if os.path.exists(dst):
                copy = _prompt_overwrite(dst)

            if copy:
                shutil.copy(src, dst)

def download_cinspect_data_archive(url=None):
    if url is None:
        url = ARCHIVE_URL

    t = tempfile.mkdtemp()
    print('Downloading sources to', t)
    filename = os.path.join(t, 'master.tar.gz')
    reporthook = lambda x, y, z: _spin(5)
    urlretrieve(url, filename, reporthook)
    print('Sources downloaded to', filename)
    return filename


def _prompt_overwrite(path):
    if sys.version_info.major > 2:
        ask = input
    else:
        ask = raw_input
    answer = ask('%s exists. Overwrite? [y/N] ' % path)
    return True if answer.strip().lower()[:1] == 'y' else False


def _spin(every, state=['|', 0]):
    if state[1] >= every:
        state[1] = 0
    if state[1] == 0:
        sigils = '|\-/'
        state[0] = sigils[(sigils.index(state[0])+1) % 4]
        sys.stderr.write('\r'+state[0])
        sys.stderr.flush()
    state[1] += 1


def main():
    copy_indexes(download_cinspect_data_archive())


if __name__ == '__main__':
    main()
