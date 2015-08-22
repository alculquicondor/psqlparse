from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import os.path

__dir__ = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.join(__dir__, '..')
postgres_includes = os.path.join(main_dir, 'postgresql/src/include')

setup(ext_modules=cythonize([
    Extension('psqlparse',
              ['psqlparse.pyx'],
              libraries=['queryparser'],
              include_dirs=[main_dir, postgres_includes],
              library_dirs=[main_dir])
]))
