cinspect
========
[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/punchagan/cinspect?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

`cinspect` is an attempt to extend Python's built-in `inspect` module to add
"inspection" for Python's builtins and other objects not written in Python.

The project is inspired by pry-doc and tries to generate indexes of the sources
for C-extensions, which are then used when obects are being inspected.

## How it works

1. We use [libclang](http://clang.llvm.org/doxygen/group__CINDEX.html)'s Python
bindings to parse the C-code and generate indexes out of it.

2. When an object is inspected, we look up the required data from the indexes
 and use it.


## Installation and Usage

NOTE: `cinspect` source code is only Python2 compatible.  We have not looked at
the compatibility of libclang's Python bindings with Python3.x.

### Installation

`cinspect` depends on having `libclang` installed in the system, for indexing
sources.  If you can obtain the indexed sources from a different location, you
will not require `libclang`.

Something like the following should do it, depending on which system you are
on.

    sudo apt-get install libclang1-3.5 libclang-common-3.5

The easiest way to install the package currently is to run (in a virtual environment).

    python setup.py develop

The `cinspect` module currently exposes only a `getsource` and `getfile`, which
are similar to equivalent functions in the built-in `inspect` module.

### Indexing your sources

The package doesn't yet bundle any indexes, and you will need to run the
indexer on your sources to index them. (In future, version specific indexes
could be packaged, a la pry-doc).

The indexer is exposed as the `cinspect-index` command.  You can run it as follows,

	cinspect-index -I/usr/lib/clang/3.5/include \
                   -I/home/punchagan/software/random/cpython/Include \
                   -I/home/punchagan/software/random/cpython/ \

				   /home/punchagan/software/random/cpython/

Essentially, you tell `cinspect-cindex` the path to the directory you wish to
index.  Since we use `libclang` to index the sources, any additional arguments
you pass to this script are passed on to `libclang`.  To get the indexer to
work, you will have to make sure that

1. `libclang` is able to find its own includes.
2. You pass-in the include dirs that the project you are indexing needs, to
compile.

The indexes are currently saved at `~/.index.json`.  Once you have created the
indexes, you can use the `getsource` or `getfile` functions exposed by
`cinspect`, to inspect your objects.

### IPython monkey-patch startup script.

We have a startup script for IPython, that monkey patches it, to enable it to
use `cinspect`.  Drop the script provided in `utils/00-cinspect.py` into your
IPython startup directory.

    cp utils/00-cinspect.py `ipython locate profile default`/startup

Now, `?` and `??` will be patched to try and use the `cinspect` indexes, once
you restart IPython (using the default profile).
