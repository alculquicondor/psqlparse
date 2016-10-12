import json

import six

from .exceptions import PSqlParseError
from .nodes import Statement
from .pg_query cimport (pg_query_parse, pg_query_free_parse_result,
                       PgQueryParseResult)


def parse(query):
    cdef bytes encoded_query
    cdef PgQueryParseResult result

    if isinstance(query, six.text_type):
        encoded_query = query.encode('utf8')
    elif isinstance(query, six.binary_type):
        encoded_query = query
    else:
        encoded_query = six.text_type(query).encode('utf8')

    result = pg_query_parse(encoded_query)

    if result.error:
        error = PSqlParseError(result.error.message.decode('utf8'),
                               result.error.lineno, result.error.cursorpos)
        pg_query_free_parse_result(result)
        raise error

    statements = [Statement(x) for x in
                  json.loads(result.parse_tree.decode('utf8'), strict=False)]
    pg_query_free_parse_result(result)
    return statements
