queryparser
===========

Installation
------------

To get things running, run the following in a checkout of this repo:

```shell
# Build PostgreSQL
git clone --depth 1 https://github.com/pganalyze/postgres.git postgresql

cd postgresql
./configure
make
cd ..

# Build Queryparser binary
./build.sh
```

The built queryparser binary is standalone and works without any PostgreSQL libraries existing or server running.

**Note:** We use a patched version of PostgreSQL, [with improvements to outfuncs.c](https://github.com/pganalyze/postgres/compare/REL9_3_STABLE...pg_query).

Usage
-----

```shell
# Parse a query into Postgres' internal format
echo 'SELECT 1' | ./queryparser

# ({SELECT :distinctClause <> :intoClause <> :targetList ({RESTARGET :name <> :indirection <> :val {A_CONST :val 1 :location 7} :location 7}) :fromClause <> :whereClause <> :groupClause <> :havingClause <> :windowClause <> :valuesLists <> :sortClause <> :limitOffset <> :limitCount <> :lockingClause <> :withClause <> :op 0 :all false :larg <> :rarg <>})

# Parse a query into JSON
echo 'SELECT 1' | ./queryparser --json

# [{"SELECT": {"distinctClause": null, "intoClause": null, "targetList": [{"RESTARGET": {"name": null, "indirection": null, "val": {"A_CONST": {"val": 1, "location": 7}}, "location": 7}}], "fromClause": null, "whereClause": null, "groupClause": null, "havingClause": null, "windowClause": null, "valuesLists": null, "sortClause": null, "limitOffset": null, "limitCount": null, "lockingClause": null, "withClause": null, "op": 0, "all": false, "larg": null, "rarg": null}}]
```

Contributors
------------

- [Michael Renner](https://github.com/terrorobe)
- [Christian Hofstaedtler](https://github.com/zeha)
- [Lukas Fittl](mailto:lukas@fittl.com)
- [Phillip Knauss](https://github.com/phillipknauss)

License
-------

Copyright (c) 2014, pganalyze Team <team@pganalyze.com><br>
queryparser is licensed under the 3-clause BSD license, see LICENSE file for details.
