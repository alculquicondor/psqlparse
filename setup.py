from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import os.path
import subprocess


class PSqlParseBuildExt(build_ext):

    def run(self):
        subprocess.call(['./queryparser/build.sh'])
        build_ext.run(self)


USE_CYTHON = bool(os.environ.get('USE_CYTHON'))

ext = '.pyx' if USE_CYTHON else '.c'

queryparser_src = os.path.join('.', 'queryparser')
postgres_src = os.path.join('.', 'postgresql', 'src')
postgres_includes = os.path.join(postgres_src, 'include')

extensions = [
    Extension('psqlparse',
              ['psqlparse' + ext],
              libraries=['queryparser', 'rt', 'pgcommon_srv',
                         'pgport_srv'],
              include_dirs=[queryparser_src, postgres_includes],
              library_dirs=[queryparser_src,
                            os.path.join(postgres_src, 'port'),
                            os.path.join(postgres_src, 'common')])
]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)

setup(name='psqlparse',
      version='0.1.2',
      url='https://github.com/alculquicondor/queryparser',
      author='Aldo Culquicondor',
      author_email='aldo@amigocloud.com',
      description='Parse SQL queries using the PostgreSQL query parser',
      license='BSD',
      platforms=['linux-x86_64'],
      cmdclass={'build_ext': PSqlParseBuildExt},
      ext_modules=extensions)
