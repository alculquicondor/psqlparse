import six
from queryparser cimport do_parse
from libc.stdlib cimport free

import json


@six.python_2_unicode_compatible
class PSqlParseError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class TargetList(object):

    def __init__(self, obj):
        self.targets = [t['RESTARGET'] for t in obj]

    def __repr__(self):
        return '<TargetList (%d)>' % len(self.targets)

    def __str__(self):
        return ', '.join('[]' for x in self.targets)


class FromClause(object):

    def __init__(self, obj):
        self.relations = [r for r in obj]

    def __repr__(self):
        return '<FromClause (%d)>' % len(self.relations)

    def __str__(self):
        return 'FROM []'


class WhereClause(object):

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return '<WhereClause (%s)>' % six.next(six.iterkeys(self.obj))

    def __str__(self):
        return 'WHERE []'


class WithClause(object):

    def __init__(self, obj):
        self.recursive = obj['WITHCLAUSE']['recursive']
        ctes = [cte['COMMONTABLEEXPR'] for cte in obj['WITHCLAUSE']['ctes']]
        self.queries = {
            cte['ctename']: Statement(cte['ctequery'])
            for cte in ctes
        }

    def __repr__(self):
        return '<WithClause (%d)>' % len(self.queries)

    def __str__(self):
        s = 'WITH '
        if self.recursive:
            s += 'RECURSIVE '
        s += ', '.join([
            '%s AS (%s)' % (name, query)
            for name, query in six.iteritems(self.queries)
        ])
        return s


class Statement(object):

    def __init__(self, obj):
        self.type = six.next(six.iterkeys(obj))
        self._obj = six.next(six.itervalues(obj))
        self.from_clause = FromClause(self._obj.get('fromClause'))\
            if self._obj.get('fromClause') else None
        self.target_list = TargetList(self._obj.get('targetList'))\
            if self._obj.get('targetList') else None
        self.where_clause = WhereClause(self._obj.get('whereClause'))\
            if self._obj.get('whereClause') else None
        self.with_clause = WithClause(self._obj.get('withClause'))\
            if self._obj.get('withClause') else None

    def __repr__(self):
        return '<Statement %s>' % self.type

    def __str__(self):
        s = ''

        if self.with_clause:
            s += str(self.with_clause) + ' '

        s += self.type

        if self.target_list:
            s += ' ' + str(self.target_list)

        if self.from_clause:
            s += ' ' + str(self.from_clause)

        if self.where_clause:
            s += ' ' + str(self.where_clause)
        return s


def parse(query):
    cdef char* output = NULL
    cdef bint error
    cdef bytes encoded_query

    if isinstance(query, six.text_type):
        encoded_query = query.encode('utf8')
    elif isinstance(query, six.binary_type):
        encoded_query = query
    else:
        encoded_query = six.text_type(query).encode('utf8')
    error = do_parse(encoded_query, &output)

    if error:
        result = output.decode('utf8')
        free(output)
        raise PSqlParseError(result)

    result = [Statement(x) for x in json.loads(output.decode('utf8'), strict=False)]
    free(output)

    return result
