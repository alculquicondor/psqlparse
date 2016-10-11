#!/bin/bash -e

if [ ! -d libpg_query ]; then
	git clone git://github.com/lfittl/libpg_query
fi

cd libpg_query
make || exit $?
