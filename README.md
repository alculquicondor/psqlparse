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
echo 'SELECT 1' | ./queryparser
```

The built queryparser binary is standalone and works without any PostgreSQL libraries existing or server running.

**Note:** We use a patched version of PostgreSQL, [with improvements to outfuncs.c](https://github.com/pganalyze/postgres/compare/REL9_3_STABLE...more-outfuncs).
