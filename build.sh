#!/bin/bash -e

cd postgresql
cd src

CPPFLAGS="-O2 -Wall -Wmissing-prototypes -Wpointer-arith -Wdeclaration-after-statement -Wendif-labels -Wmissing-format-attribute -Wformat-security -fno-strict-aliasing -fwrapv"

LIBFLAGS="-lm"
if [ `uname` != "Darwin" ]; then
	LIBFLAGS+=" -lrt -ldl"
fi

OBJFILES=`find backend -name '*.o' | egrep -v '(main/main\.o|snowball|libpqwalreceiver|conversion_procs)' | xargs echo`
OBJFILES+=" timezone/localtime.o timezone/strftime.o timezone/pgtz.o"
OBJFILES+=" common/libpgcommon_srv.a port/libpgport_srv.a"

gcc $CPPFLAGS -Lport -Lcommon -I include ../../queryparser.c $OBJFILES $LIBFLAGS -o ../../queryparser
