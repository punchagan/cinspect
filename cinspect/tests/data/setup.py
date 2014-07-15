from distutils.core import setup, Extension

hello_module = Extension('hello', sources = ['hellomodule.c'])

setup(
    name = 'PackageName',
    version = '1.0',
    description = 'This is a demo package',
    ext_modules = [hello_module]
)
