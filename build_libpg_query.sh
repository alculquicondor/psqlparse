#!/bin/bash -e

LIBPGQUERYDIR='libpg_query-9.5-latest'
LIBPGQUERYZIP='libpg_query-9.5-latest.zip'

if [ ! -d $LIBPGQUERYDIR ]; then
    curl -L -o $LIBPGQUERYZIP https://github.com/lfittl/libpg_query/archive/9.5-latest.zip
    unzip $LIBPGQUERYZIP
fi

cd $LIBPGQUERYDIR
make || exit $?
