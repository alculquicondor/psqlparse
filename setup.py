from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import os.path
import subprocess
import sys
import platform


class PSqlParseBuildExt(build_ext):

    def run(self):
        return_code = subprocess.call(['./queryparser/build.sh'])
        if return_code:
            sys.stderr.write('''
An error occurred during extension building.
Make sure you have bison and flex installed on your system.
''')
            sys.exit(return_code)
        build_ext.run(self)


USE_CYTHON = bool(os.environ.get('USE_CYTHON'))

ext = '.pyx' if USE_CYTHON else '.c'

queryparser_src = os.path.join('.', 'queryparser')
postgres_src = os.path.join('.', 'postgresql', 'src')
postgres_includes = os.path.join(postgres_src, 'include')

libraries = ['queryparser', 'pgcommon_srv', 'pgport_srv']
if platform.uname()[0] != 'Darwin':
    libraries.append('rt')

extensions = [
    Extension('psqlparse',
              ['psqlparse' + ext],
              libraries=libraries,
              include_dirs=[queryparser_src, postgres_includes],
              library_dirs=[queryparser_src,
                            os.path.join(postgres_src, 'port'),
                            os.path.join(postgres_src, 'common')])
]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)

setup(name='psqlparse',
      version='0.1.7',
      url='https://github.com/alculquicondor/queryparser',
      author='Aldo Culquicondor',
      author_email='aldo@amigocloud.com',
      description='Parse SQL queries using the PostgreSQL query parser',
      install_requires=['six'],
      license='BSD',
      cmdclass={'build_ext': PSqlParseBuildExt},
      ext_modules=extensions)
