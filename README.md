psqlparse
=========

This Python module  uses the actual PostgreSQL server source to parse SQL
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
psqlparse.parse('SELECT * from mytable')
```

Contributors
------------

- [Aldo Culquicondor](https://github.com/alculquicondor/)
