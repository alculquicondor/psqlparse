class Value(object):
    pass


class String(Value):

    def __init__(self, obj):
        self.str = obj.get('str')


class RangeVar(object):

    def __init__(self, obj):
        """
        Range variable, used in FROM clauses

        Also used to represent table names in utility statements; there,
        the alias field is not used, and inhOpt shows whether to apply the
        operation recursively to child tables.
        """

        self.catalogname = obj.get('catalogname')
        self.schemaname = obj.get('schemaname')
        self.relname = obj.get('relname')
        self.inh_opt = obj.get('inhOpt')
        self.relpersistence = obj.get('relpersistence')
        self.alias = obj.get('alias')
        self.location = obj['location']

    def __repr__(self):
        return '<RangeVar (%s)>' % self.relname

    def __str__(self):
        return '%s' % self.relname


class JoinExpr(object):
    """
    For SQL JOIN expressions
    """

    def __init__(self, obj):
        self.jointype = obj['jointype']
        self.is_natural = bool(obj.get('isNatural'))
        self.larg = obj['larg']
        self.rarg = obj['rarg']
        self.using_clause = obj.get('using_clause')
        self.quals = obj.get('quals')
        self.alias = obj.get('Alias')

    def __repr__(self):
        return '<JoinExpr type=%s>' % self.jointype

    def __str__(self):
        return '[] JOIN [] ON ()'


class IntoClause(object):

    def __init__(self, obj):
        self._obj = obj
