import six

from .primnodes import NODE_MAP


class TargetList(object):

    def __init__(self, obj):
        self.targets = [t['ResTarget'] for t in obj]

    def __repr__(self):
        return '<TargetList (%d)>' % len(self.targets)

    def __str__(self):
        return ', '.join('[]' for x in self.targets)


class FromClause(object):
    """
    To be deprecated in v1.0 so that it is replaced by a simple list
    """

    def __init__(self, items):
        self.items = []
        for item in items:
            key, value = six.next(six.iteritems(item))
            self.items.append(NODE_MAP[key](item[key]) if key in NODE_MAP
                              else item)

    def __repr__(self):
        return '<FromClause (%d)>' % len(self.items)

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
        self.recursive = obj['WithClause'].get('recursive')
        ctes = ([cte['CommonTableExpr'] for cte in
                 obj['WithClause']['ctes']])
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
        s += ', '.join(
            ['%s AS (%s)' % (name, query)
             for name, query in six.iteritems(self.queries)])
        return s


class Statement(object):

    def __init__(self, obj):
        self.type = six.next(six.iterkeys(obj))
        self._obj = six.next(six.itervalues(obj))
        self.from_clause = (FromClause(self._obj.get('fromClause'))
                            if 'fromClause' in self._obj else None)
        self.target_list = (TargetList(self._obj.get('targetList'))
                            if 'targetList' in self._obj else None)
        self.where_clause = (WhereClause(self._obj.get('whereClause'))
                             if 'whereClause' in self._obj else None)
        self.with_clause = (WithClause(self._obj.get('withClause'))
                            if 'withClause' in self._obj else None)

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
