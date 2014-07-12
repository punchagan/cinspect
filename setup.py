from setuptools import setup
from distutils.util import convert_path

# Additional keyword arguments for setup
kwargs = {}

d = {}
execfile(convert_path('cinspect/__init__.py'), d)
kwargs['version'] = d['__version__']

with open('README.md') as f:
    kwargs['long_description'] = f.read()


packages = [
    'cinspect',
    'cinspect.index',
    'cinspect.tests',
    'cinspect.vendor.clang',
]

package_data = {}

setup(
    name="cinspect",
    author="Puneeth Chaganti",
    author_email="punchagan@muse-amuse.in",
    url = "https://github.com/punchagan/cinspect",
    license="BSD",
    description = "C-source introspection for packages.",
    packages = packages,
    package_data=package_data,
    entry_points = {
        "console_scripts": [
             "cinspect-index = cinspect.index.writer:main",
        ],
    },
    **kwargs
)
