#include <string.h>

#include "queryparser.h"


const char* progname = "queryparser";
int do_parse(const char* query, char** output)
{
	MemoryContext ctx;
	List *tree;
	int error = 1;

	ctx = AllocSetContextCreate(TopMemoryContext,
								"RootContext",
								ALLOCSET_DEFAULT_MINSIZE,
								ALLOCSET_DEFAULT_INITSIZE,
								ALLOCSET_DEFAULT_MAXSIZE);
	MemoryContextSwitchTo(ctx);

	PG_TRY();
	{
		tree = raw_parser(query);

		if (tree != NULL)
		{
			char* t = nodeToJSONString(tree);
			*output = (char*) malloc(strlen(t) + 1);
			strcpy(*output, t);
			pfree(t);
			error = 0;
		}
	}
	PG_CATCH();
	{
		ErrorData* error = CopyErrorData();
		*output = (char *) malloc(strlen(error->message) + 10);
		sprintf(*output, "%s (pos:%d)", error->message, error->cursorpos);
	}
	PG_END_TRY();


	MemoryContextSwitchTo(TopMemoryContext);
	MemoryContextDelete(ctx);

	return error;
}

void __attribute__ ((constructor)) init() {
	MemoryContextInit();
}
