import abc

from .utils import build_from_item


class Value(object):
    __metaclass__ = abc.ABCMeta

    def __str__(self):
        return str(self.val)

    @abc.abstractproperty
    def val(self):
        pass


class Integer(Value):

    def __init__(self, obj):
        self.ival = obj.get('ival')

    def __int__(self):
        return self.ival

    @property
    def val(self):
        return self.ival


class String(Value):

    def __init__(self, obj):
        self.str = obj.get('str')

    @property
    def val(self):
        return self.str


class Float(Value):

    def __init__(self, obj):
        self.str = obj.get('str')
        self.fval = float(self.str)

    def __float__(self):
        return self.fval

    @property
    def val(self):
        return self.fval


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
        self.jointype = obj.get('jointype')
        self.is_natural = obj.get('isNatural')
        self.larg = build_from_item(obj, 'larg')
        self.rarg = build_from_item(obj, 'rarg')
        self.using_clause = build_from_item(obj, 'usingClause')
        self.quals = build_from_item(obj, 'quals')
        self.alias = build_from_item(obj, 'alias')

    def __repr__(self):
        return '<JoinExpr type=%s>' % self.jointype

    def __str__(self):
        return '%s JOIN %s ON ()' % (self.larg, self.rarg)


class Alias(object):

    def __init__(self, obj):
        self.aliasname = obj.get('aliasname')
        self.colnames = build_from_item(obj, 'colnames')


class IntoClause(object):

    def __init__(self, obj):
        self._obj = obj


class BoolExpr(object):

    def __init__(self, obj):
        self.xpr = obj.get('xpr')
        self.boolop = obj.get('boolop')
        self.args = build_from_item(obj, 'args')
        self.location = obj.get('location')
