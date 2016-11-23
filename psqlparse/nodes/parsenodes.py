import six

from .utils import build_from_item


class Statement(object):

    statement = ''

    def __str__(self):
        return self.statement


class SelectStmt(Statement):

    statement = 'SELECT'

    def __init__(self, obj):
        self.distinct_clause = build_from_item(obj, 'distinctClause')
        self.into_clause = build_from_item(obj, 'intoClause')
        self.target_list = build_from_item(obj, 'targetList')
        self.from_clause = build_from_item(obj, 'fromClause')
        self.where_clause = build_from_item(obj, 'whereClause')
        self.group_clause = build_from_item(obj, 'groupClause')
        self.having_clause = build_from_item(obj, 'havingClause')
        self.window_clause = build_from_item(obj, 'windowClause')

        self.values_lists = build_from_item(obj, 'valuesLists')

        self.sort_clause = build_from_item(obj, 'sortClause')
        self.limit_offset = build_from_item(obj, 'limitOffset')
        self.locking_clause = build_from_item(obj, 'locking_Clause')
        self.with_clause = build_from_item(obj, 'withClause')

        self.op = obj.get('op')
        self.bool = obj.get('all')
        self.larg = build_from_item(obj, 'larg')
        self.rarg = build_from_item(obj, 'rarg')


class InsertStmt(Statement):

    statement = 'INSERT INTO'

    def __init__(self, obj):
        pass


class UpdateStmt(Statement):

    statement = 'UPDATE'

    def __init__(self, obj):
        pass


class DeleteStmt(Statement):

    statement = 'DELETE FROM'

    def __init__(self, obj):
        pass


class WithClause(object):

    def __init__(self, obj):
        self.ctes = build_from_item(obj, 'ctes')
        self.recursive = obj.get('recursive')
        self.location = obj.get('location')

    def __repr__(self):
        return '<WithClause (%d)>' % len(self.ctes)

    def __str__(self):
        s = 'WITH '
        if self.recursive:
            s += 'RECURSIVE '
        s += ', '.join(
            ['%s AS (%s)' % (name, query)
             for name, query in six.iteritems(self.ctes)])
        return s


class CommonTableExpr(object):

    def __init__(self, obj):
        self.ctename = obj.get('ctename')
        self.aliascolnames = build_from_item(obj, 'aliascolnames')
        self.ctequery = build_from_item(obj, 'ctequery')
        self.location = obj.get('location')
        self.cterecursive = obj.get('cterecursive')
        self.cterefcount = obj.get('cterefcount')
        self.ctecolnames = build_from_item(obj, 'ctecolnames')
        self.ctecoltypes = build_from_item(obj, 'ctecoltypes')
        self.ctecoltypmods = build_from_item(obj, 'ctecoltypmods')
        self.ctecolcollations = build_from_item(obj, 'ctecolcollations')


class RangeSubselect(object):

    def __init__(self, obj):
        self.lateral = obj.get('lateral')
        self.subquery = build_from_item(obj, 'subquery')
        self.alias = build_from_item(obj, 'alias')


class ResTarget(object):

    def __init__(self, obj):
        self.name = obj.get('name')
        self.indirection = build_from_item(obj, 'indirection')
        self.val = build_from_item(obj, 'val')
        self.location = obj.get('location')


class ColumnRef(object):

    def __init__(self, obj):
        self.fields = build_from_item(obj, 'fields')
        self.location = obj.get('location')


class AStar(object):

    def __init__(self, obj):
        pass


class AExpr(object):

    def __init__(self, obj):
        self.kind = obj.get('kind')
        self.name = build_from_item(obj, 'name')
        self.lexpr = build_from_item(obj, 'lexpr')
        self.rexpr = build_from_item(obj, 'rexpr')
        self.location = obj.get('location')


class AConst(object):

    def __init__(self, obj):
        self.val = build_from_item(obj, 'val')
        self.location = obj.get('location')
