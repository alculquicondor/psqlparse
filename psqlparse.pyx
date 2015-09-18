from queryparser cimport do_parse
from libc.stdlib cimport free

import json


class PSqlParseError(Exception):

    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return self.value

    def __str__(self):
        return self.value.encode('utf8')


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
        return '<WhereClause (%s)>' % self.obj.iterkeys().next()

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
            for name, query in self.queries.iteritems()
        ])
        return s


class Statement(object):

    def __init__(self, obj):
        self.type = obj.iterkeys().next()
        self._obj = obj.itervalues().next()
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
    cdef str encoded_query

    encoded_query = query.encode('utf8') if isinstance(query, unicode)\
        else str(query)
    error = do_parse(encoded_query, &output)

    if error:
        result = output.decode('utf8')
        free(output)
        raise PSqlParseError(result)

    result = [Statement(x) for x in json.loads(output, strict=False)]
    free(output)

    return result
