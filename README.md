To get things running:

 * git clone git://git.postgresql.org/git/postgresql.git
 * cd ~postgresql
 * ./configure
 * make
 * cd src/backend
```
gcc -O2 -Wall -Wmissing-prototypes -Wpointer-arith -Wdeclaration-after-statement -Wendif-labels -Wmissing-format-attribute -Wformat-security -fno-strict-aliasing -fwrapv -L../../src/port -L../../src/common -I ../include ../../../queryparser/queryparser.c `find . -name '*.o' | egrep -v '(main/main\.o|snowball|libpqwalreceiver|conversion_procs)' | xargs echo` ../timezone/localtime.o ../timezone/strftime.o ../timezone/pgtz.o ../common/libpgcommon_srv.a ../port/libpgport_srv.a -lm -o /tmp/queryparser -lrt -ldl
```
 * on os x remove -lrt and -ldl
 * echo 'SELECT 1' | /tmp/queryparser
