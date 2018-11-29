import json

import six

from .nodes.utils import build_from_obj
from .exceptions import PSqlParseError
from .pg_query cimport (
    pg_query_parse,
    pg_query_fingerprint,
    pg_query_free_parse_result,
    pg_query_free_fingerprint_result,
    PgQueryParseResult,
    PgQueryFingerprintResult,
)


def _encode_query(query):
    if isinstance(query, six.text_type):
        return query.encode('utf8')
    elif isinstance(query, six.binary_type):
        return query
    else:
        return six.text_type(query).encode('utf8')


def parse_dict(query):
    cdef bytes encoded_query = _encode_query(query)
    cdef PgQueryParseResult result

    result = pg_query_parse(encoded_query)
    if result.error:
        error = PSqlParseError(result.error.message.decode('utf8'),
                               result.error.lineno, result.error.cursorpos)
        pg_query_free_parse_result(result)
        raise error

    statement_dicts = json.loads(result.parse_tree.decode('utf8'),
                                 strict=False)
    pg_query_free_parse_result(result)
    return statement_dicts


def parse(query):
    return [build_from_obj(obj) for obj in parse_dict(query)]


def fingerprint(query):
    cdef bytes encoded_query = _encode_query(query)
    cdef PgQueryFingerprintResult result
    result = pg_query_fingerprint(encoded_query)
    if result.error:
        error = PSqlParseError(result.error.message.decode('utf8'),
                               result.error.lineno, result.error.cursorpos)
        pg_query_free_fingerprint_result(result)
        raise error
    hexdigest = result.hexdigest.decode('utf-8')
    pg_query_free_fingerprint_result(result)
    return hexdigest
