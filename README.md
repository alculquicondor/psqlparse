queryparser
===========

Installation
------------

To get things running, run the following in a checkout of this repo:

```shell
# Build PostgreSQL
git clone --depth 1 https://github.com/pganalyze/postgres.git postgresql

cd postgresql
CFLAGS=-fPIC ./configure
make
cd ..

# Build Queryparser static library
./build.sh
```

The built queryparser binary is standalone and works without any PostgreSQL libraries existing or server running.

If you also want to build and install the python module:

```shell
# load your virtualenv
cd psqlparse
python setup.py install
```

**Note:** We use a patched version of PostgreSQL, [with improvements to outfuncs.c](https://github.com/pganalyze/postgres/compare/REL9_3_STABLE...pg_query).

Contributors
------------

- [Michael Renner](https://github.com/terrorobe)
- [Christian Hofstaedtler](https://github.com/zeha)
- [Lukas Fittl](mailto:lukas@fittl.com)
- [Phillip Knauss](https://github.com/phillipknauss)
- [Aldo Culquicondor](https://github.com/alculquicondor)

License
-------

Copyright (c) 2014, pganalyze Team <team@pganalyze.com><br>
queryparser is licensed under the 3-clause BSD license, see LICENSE file for details.
