from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import os.path

main_dir = '..'
postgres_includes = os.path.join(main_dir, 'postgresql/src/include')

setup(name='psqlparse',
      version='0.1',
      url='https://github.com/alculquicondor/queryparser',
      author='Aldo Culquicondor',
      author_email='aldo@amigocloud.com',
      license='BSD',
      ext_modules=cythonize([
          Extension('psqlparse',
                    ['psqlparse.pyx'],
                    libraries=['queryparser'],
                    include_dirs=[main_dir, postgres_includes],
                    library_dirs=[main_dir])
      ]),
      data_files=[('lib', ['libqueryparser.so'])])
