#include "postgres.h"

#include "utils/memutils.h"
#include "parser/parser.h"
#include "nodes/print.h"

int do_parse(const char* query, char** output);

void init(void);
