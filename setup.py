import re
from setuptools import setup
from distutils.util import convert_path

def get_version():
    with open(convert_path('cinspect/__init__.py')) as f:
        metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", f.read()))
        return metadata.get('version', '0.1')

def get_long_description():
    with open('README.md') as f:
        return f.read()


packages = [
    'cinspect',
    'cinspect.index',
    'cinspect.tests',
    'cinspect.vendor.clang',
]

package_data = {
    'cinspect.tests': ['data/*.md', 'data/*.c', 'data/*.py'],
}

setup(
    name="cinspect",
    author="Puneeth Chaganti",
    author_email="punchagan@muse-amuse.in",
    version=get_version(),
    long_description=get_long_description(),
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
)
