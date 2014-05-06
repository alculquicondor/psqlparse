To get things running, run the following in a checkout of this repo:

```
# Build PostgreSQL
git clone --shallow https://github.com/pganalyze/postgres.git postgresql

cd postgresql
./configure
make
cd ..

# Build Queryparser binary
./build.sh

# Test it :)
echo 'SELECT 1' | queryparser
```

The built queryparser binary is standalone and works without any PostgreSQL libraries existing or server running.

Note: We use a patched version of PostgreSQL (as referenced above) with changes to outfuncs.c that:

* Add support for INSERT/DELETE/UPDATE statements
* Add length information to constants

It is recommended you use it as well.