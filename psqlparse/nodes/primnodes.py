from .utils import build_from_item
from .nodes import Node
from .value import Name


class RangeVar(Node):

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
        self.alias = build_from_item(obj, 'alias')
        self.location = obj['location']

    def __repr__(self):
        return '<RangeVar (%s)>' % self.relname

    def __str__(self):
        return '%s' % self.relname

    def tables(self):
        components = [
            getattr(self, name) for name in ('schemaname', 'relname')
            if getattr(self, name, None) is not None
        ]
        return {'.'.join(components)}


class JoinExpr(Node):
    """
    For SQL JOIN expressions
    """

    def __init__(self, obj):
        self.jointype = obj.get('jointype')
        self.is_natural = obj.get('isNatural')
        self.larg = build_from_item(obj, 'larg')
        self.rarg = build_from_item(obj, 'rarg')
        self.using_clause = build_from_item(obj, 'usingClause', 'Literal')
        self.quals = build_from_item(obj, 'quals')
        self.alias = build_from_item(obj, 'alias')

    def __repr__(self):
        return '<JoinExpr type=%s>' % self.jointype

    def __str__(self):
        return '%s JOIN %s ON ()' % (self.larg, self.rarg)

    def tables(self):
        return self.larg.tables() | self.rarg.tables()


class Alias(Node):

    def __init__(self, obj):
        self.aliasname = Name.from_string(obj.get('aliasname'))
        self.colnames = build_from_item(obj, 'colnames', 'Name')

    def tables(self):
        return set()


class IntoClause(Node):

    def __init__(self, obj):
        self._obj = obj


class Expr(Node):
    """
    Expr - generic superclass for executable-expression nodes
    """


class BoolExpr(Expr):

    def __init__(self, obj):
        self.boolop = obj.get('boolop')
        self.args = build_from_item(obj, 'args')
        self.location = obj.get('location')

    def tables(self):
        _tables = set()
        for item in self.args:
            _tables |= item.tables()
        return _tables


class SubLink(Expr):

    def __init__(self, obj):
        self.sub_link_type = obj.get('subLinkType')
        self.sub_link_id = obj.get('subLinkId')
        self.testexpr = build_from_item(obj, 'testexpr')
        self.oper_name = build_from_item(obj, 'operName')
        self.subselect = build_from_item(obj, 'subselect')
        self.location = obj.get('location')

    def tables(self):
        return self.subselect.tables()
