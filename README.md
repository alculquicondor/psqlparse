psqlparse
=========
[![Build Status](https://travis-ci.org/alculquicondor/psqlparse.svg?branch=master)](https://travis-ci.org/alculquicondor/psqlparse)

**This project is not maintained anymore**. If you would like to maintain it, send me a DM in twitter @alculquicondor.

This Python module  uses the [libpg\_query](https://github.com/lfittl/libpg_query) to parse SQL
queries and return the internal PostgreSQL parsetree.

Installation
------------

```shell
pip install psqlparse
```

Usage
-----

```python
import psqlparse
statements = psqlparse.parse('SELECT * from mytable')
used_tables = statements[0].tables()  # ['my_table']
```

`tables` is only available from version 1.0rc1

Development
-----------

0. Update dependencies

```shell
git submodule update --init
```

1. Install requirements:

```shell
pip install -r requirements.txt
```

2. Build Cython extension

```shell
USE_CYTHON=1 python setup.py build_ext --inplace
```

3. Perform changes

4. Run tests

```shell
pytest
```

Maintainers
------------

- [Aldo Culquicondor](https://github.com/alculquicondor/)
- [Kevin Zúñiga](https://github.com/kevinzg/)
