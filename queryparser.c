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
bool do_parse(const char* query, char* (*str_fun)(const void*) );

bool do_parse(const char* query, char* (*str_fun)(const void*) )
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
		//s = nodeToJSONString(tree);
		s = str_fun(tree);

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

	if (argc > 1 && 
		(strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0))
	{
		pritnf("USAGE: queryparser\nOPTIONS:\n\t--json: Output in JSON format\n\t--help: Show this help\n");
		return 0;
	}
	if (argc > 1 && strcmp(argv[1], "--json") == 0)
	{
		return do_parse(line, &nodeToJSONString) ? 0 : 1;
	}
	return do_parse(line, &nodeToString) ? 0 : 1;
}
