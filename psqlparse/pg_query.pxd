cdef extern from "pg_query.h":

    ctypedef struct PgQueryError:
        char *message
        int lineno
        int cursorpos

    ctypedef struct PgQueryParseResult:
        char *parse_tree
        PgQueryError *error

    ctypedef struct PgQueryNormalizeResult:
        char *normalized_query
        PgQueryError *error

    PgQueryParseResult pg_query_parse(const char* input)

    void pg_query_free_parse_result(PgQueryParseResult result);

    PgQueryNormalizeResult pg_query_normalize(const char* input)

    void pg_query_free_normalize_result(PgQueryNormalizeResult result);
