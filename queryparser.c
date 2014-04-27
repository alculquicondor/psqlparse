#include "postgres.h"

#include <ctype.h>
#include <float.h>
#include <math.h>
#include <limits.h>
#include <unistd.h>
#include <sys/stat.h>
#include "utils/memutils.h"

#include "parser/parser.h"
#include "nodes/print.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

const char* progname = "testit";
bool do_parse(const char* query);

bool do_parse(const char* query)
{
	MemoryContext ctx = NULL;
	List *tree;

	ctx = AllocSetContextCreate(TopMemoryContext,
								"RootContext",
								ALLOCSET_DEFAULT_MINSIZE,
								ALLOCSET_DEFAULT_INITSIZE,
								ALLOCSET_DEFAULT_MAXSIZE);
	MemoryContextSwitchTo(ctx);

	tree = raw_parser(query);

	if (tree != NULL)
	{
		char *s;
		s = nodeToString(tree);

		printf("%s\n", s);

		pfree(s);
	}

	MemoryContextSwitchTo(TopMemoryContext);
	MemoryContextDelete(ctx);

	return (tree != NULL);
}

#define BUFSIZE 32768

int main(int argc, char **argv)
{
	char  line[BUFSIZE];
	char* p_nl;
	MemoryContextInit();

	if (!fgets(line, BUFSIZE, stdin))
		return 2;  /* no data read */

	p_nl = strchr(line, (int) '\n');
	if (p_nl != NULL) {
		*(p_nl) = '\0';
	} else {
		return 3; /* no newline */
	}

	if (line[0] == '#' || line[0] == '\0')
		return 1;

	do_parse(line);

	return 0;
}
