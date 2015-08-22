from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import os.path

main_dir = '..'
postgres_src = os.path.join(main_dir, 'postgresql/src')
postgres_includes = os.path.join(postgres_src, 'include')

setup(name='psqlparse',
      version='0.1',
      url='https://github.com/alculquicondor/queryparser',
      author='Aldo Culquicondor',
      author_email='aldo@amigocloud.com',
      license='BSD',
      ext_modules=cythonize([
          Extension('psqlparse',
                    ['psqlparse.pyx'],
                    libraries=['queryparser', 'rt', 'pgcommon_srv',
                               'pgport_srv'],
                    include_dirs=[main_dir, postgres_includes],
                    library_dirs=[main_dir,
                                  os.path.join(postgres_src, 'port'),
                                  os.path.join(postgres_src, 'common')])
      ]),
      data_files=[('lib', ['libqueryparser.so'])])
