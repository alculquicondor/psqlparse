psqlparse
=========
[![Build Status](https://travis-ci.org/alculquicondor/psqlparse.svg?branch=master)](https://travis-ci.org/alculquicondor/psqlparse)

This Python module uses the [libpg\_query](https://github.com/lfittl/libpg_query) to parse SQL
queries and return the internal PostgreSQL parsetree.

Built on that, there is a _pretty print_ feature that can be used to reformat a statement into
an equivalent and nicely indented representation.

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

The *parsetree* returned by ``parse()`` can be serialized back into a raw SQL:

```python
print(psqlparse.serialize(statements))
```

that emits:

```sql
SELECT * FROM mytable
```

or you can obtain its pretty representation::

```python
print(psqlparse.format('SELECT a.id, b.value'
                       ' from mytable a join other b using (id)'
                       ' where a.id > 0 and a.id < 10'))
```

that produces:

```sql
SELECT a.id
     , b.value
FROM mytable AS a
  INNER JOIN other AS b USING (id)
WHERE a.id > 0
  AND a.id < 10
```

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
