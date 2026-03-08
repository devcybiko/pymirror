from setuptools import setup, Extension

clib_module = Extension(
    'clib',
    sources=['clib.c'],
)

setup(
    name='clib',
    version='1.0',
    description='C library for image conversion',
    ext_modules=[clib_module],
    zip_safe=False,
)