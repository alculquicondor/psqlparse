This fork adds the --json switch which outputs the parse tree in JSON instead of the raw parse tree.

To get things running, run the following in a checkout of this repo:

```
# Build PostgreSQL
git clone --depth 1 https://github.com/pganalyze/postgres.git postgresql

cd postgresql
./configure
make
cd ..

# Build Queryparser binary
./build.sh

# Test it :)
echo 'SELECT 1' | ./queryparser

# Test it with JSON 
echo 'SELECT 1' | ./queryparser --json
```

The built queryparser binary is standalone and works without any PostgreSQL libraries existing or server running.

**Note:** We use a patched version of PostgreSQL, [with improvements to outfuncs.c](https://github.com/pganalyze/postgres/compare/REL9_3_STABLE...more-outfuncs).
