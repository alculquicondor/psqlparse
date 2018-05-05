psqlparse
=========
[![Build Status](https://travis-ci.org/alculquicondor/psqlparse.svg?branch=master)](https://travis-ci.org/alculquicondor/psqlparse)

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

Contributors
------------

- [Aldo Culquicondor](https://github.com/alculquicondor/)
