import six

from .utils import build_from_item
from .nodes import Node


class Statement(Node):

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
        self.limit_count = build_from_item(obj, 'limitCount')
        self.locking_clause = build_from_item(obj, 'lockingClause')
        self.with_clause = build_from_item(obj, 'withClause')

        self.op = obj.get('op')
        self.all = obj.get('all')
        self.larg = build_from_item(obj, 'larg')
        self.rarg = build_from_item(obj, 'rarg')

    def tables(self):
        _tables = set()
        if self.target_list:
            for item in self.target_list:
                _tables |= item.tables()
        if self.from_clause:
            for item in self.from_clause:
                _tables |= item.tables()
        if self.where_clause:
            _tables |= self.where_clause.tables()
        if self.with_clause:
            _tables |= self.with_clause.tables()

        if self.larg:
            _tables |= self.larg.tables()
        if self.rarg:
            _tables |= self.rarg.tables()

        return _tables


class InsertStmt(Statement):

    statement = 'INSERT INTO'

    def __init__(self, obj):
        self.relation = build_from_item(obj, 'relation')
        self.cols = build_from_item(obj, 'cols')
        self.select_stmt = build_from_item(obj, 'selectStmt')
        self.on_conflict_clause = build_from_item(obj, 'onConflictClause')
        self.returning_list = build_from_item(obj, 'returningList')
        self.with_clause = build_from_item(obj, 'withClause')

    def tables(self):
        _tables = self.relation.tables() | self.select_stmt.tables()

        if self.with_clause:
            _tables |= self.with_clause.tables()

        return _tables


class UpdateStmt(Statement):

    statement = 'UPDATE'

    def __init__(self, obj):
        self.relation = build_from_item(obj, 'relation')
        self.target_list = build_from_item(obj, 'targetList')
        self.where_clause = build_from_item(obj, 'whereClause')
        self.from_clause = build_from_item(obj, 'fromClause')
        self.returning_list = build_from_item(obj, 'returningList')
        self.with_clause = build_from_item(obj, 'withClause')

    def tables(self):
        _tables = self.relation.tables()

        if self.where_clause:
            _tables |= self.where_clause.tables()
        if self.from_clause:
            for item in self.from_clause:
                _tables |= item.tables()
        if self.with_clause:
            _tables |= self.with_clause.tables()

        return _tables


class DeleteStmt(Statement):

    statement = 'DELETE FROM'

    def __init__(self, obj):
        self.relation = build_from_item(obj, 'relation')
        self.using_clause = build_from_item(obj, 'usingClause')
        self.where_clause = build_from_item(obj, 'whereClause')
        self.returning_list = build_from_item(obj, 'returningList')
        self.with_clause = build_from_item(obj, 'withClause')

    def tables(self):
        _tables = self.relation.tables()

        if self.using_clause:
            for item in self.using_clause:
                _tables |= item.tables()
        if self.where_clause:
            _tables |= self.where_clause.tables()
        if self.with_clause:
            _tables |= self.with_clause.tables()

        return _tables


class WithClause(Node):

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

    def tables(self):
        _tables = set()
        for item in self.ctes:
            _tables |= item.tables()
        return _tables


class CommonTableExpr(Node):

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

    def tables(self):
        return self.ctequery.tables()


class RangeSubselect(Node):

    def __init__(self, obj):
        self.lateral = obj.get('lateral')
        self.subquery = build_from_item(obj, 'subquery')
        self.alias = build_from_item(obj, 'alias')

    def tables(self):
        return self.subquery.tables()


class ResTarget(Node):
    """
    Result target.

    In a SELECT target list, 'name' is the column label from an
    'AS ColumnLabel' clause, or NULL if there was none, and 'val' is the
    value expression itself.  The 'indirection' field is not used.

    INSERT uses ResTarget in its target-column-names list.  Here, 'name' is
    the name of the destination column, 'indirection' stores any subscripts
    attached to the destination, and 'val' is not used.

    In an UPDATE target list, 'name' is the name of the destination column,
    'indirection' stores any subscripts attached to the destination, and
    'val' is the expression to assign.
    """

    def __init__(self, obj):
        self.name = obj.get('name')
        self.indirection = build_from_item(obj, 'indirection')
        self.val = build_from_item(obj, 'val')
        self.location = obj.get('location')

    def tables(self):
        _tables = set()
        if isinstance(self.val, list):
            for item in self.val:
                _tables |= item.tables()
        elif isinstance(self.val, Node):
            _tables |= self.val.tables()

        return _tables


class ColumnRef(Node):

    def __init__(self, obj):
        self.fields = build_from_item(obj, 'fields')
        self.location = obj.get('location')

    def tables(self):
        return set()


class FuncCall(Node):

    def __init__(self, obj):
        self.funcname = build_from_item(obj, 'funcname')
        self.args = build_from_item(obj, 'args')
        self.agg_order = build_from_item(obj, 'agg_order')
        self.agg_filter = build_from_item(obj, 'agg_filter')
        self.agg_within_group = obj.get('agg_within_group')
        self.agg_star = obj.get('agg_star')
        self.agg_distinct = obj.get('agg_distinct')
        self.func_variadic = obj.get('func_variadic')
        self.over = build_from_item(obj, 'over')
        self.location = obj.get('location')

    def tables(self):
        _tables = set()
        if self.args:
            for item in self.args:
                _tables |= item.tables()
        return _tables


class AStar(Node):

    def __init__(self, obj):
        pass

    def tables(self):
        return set()


class AExpr(Node):

    def __init__(self, obj):
        self.kind = obj.get('kind')
        self.name = build_from_item(obj, 'name')
        self.lexpr = build_from_item(obj, 'lexpr')
        self.rexpr = build_from_item(obj, 'rexpr')
        self.location = obj.get('location')

    def tables(self):
        _tables = set()

        if isinstance(self.lexpr, list):
            for item in self.lexpr:
                _tables |= item.tables()
        elif isinstance(self.lexpr, Node):
            _tables |= self.lexpr.tables()

        if isinstance(self.rexpr, list):
            for item in self.rexpr:
                _tables |= item.tables()
        elif isinstance(self.rexpr, Node):
            _tables |= self.rexpr.tables()

        return _tables


class AConst(Node):

    def __init__(self, obj):
        self.val = build_from_item(obj, 'val')
        self.location = obj.get('location')

    def tables(self):
        return set()


class TypeCast(Node):

    def __init__(self, obj):
        self.arg = build_from_item(obj, 'arg')
        self.type_name = build_from_item(obj, 'typeName')
        self.location = obj.get('location')


class TypeName(Node):

    def __init__(self, obj):
        self.names = build_from_item(obj, 'names')
        self.type_oid = obj.get('typeOid')
        self.setof = obj.get('setof')
        self.pct_type = obj.get('pct_type')
        self.typmods = build_from_item(obj, 'typmods')
        self.typemod = obj.get('typemod')
        self.array_bounds = build_from_item(obj, 'arrayBounds')
        self.location = obj.get('location')


class SortBy(Node):

    def __init__(self, obj):
        self.node = build_from_item(obj, 'node')
        self.sortby_dir = obj.get('sortby_dir')
        self.sortby_nulls = obj.get('sortby_nulls')
        self.use_op = build_from_item(obj, 'useOp')
        self.location = obj.get('location')


class WindowDef(Node):

    def __init__(self, obj):
        self.name = obj.get('name')
        self.refname = obj.get('refname')
        self.partition_clause = build_from_item(obj, 'partitionClause')
        self.order_clause = build_from_item(obj, 'orderClause')
        self.frame_options = obj.get('frameOptions')
        self.start_offset = build_from_item(obj, 'startOffset')
        self.end_offset = build_from_item(obj, 'endOffset')
        self.location = obj.get('location')


class LockingClause(Node):

    def __init__(self, obj):
        self.locked_rels = build_from_item(obj, 'lockedRels')
        self.strength = build_from_item(obj, 'strength')
        self.wait_policy = obj.get('waitPolicy')


class RangeFunction(Node):

    def __init__(self, obj):
        self.lateral = obj.get('lateral')
        self.ordinality = obj.get('ordinality')
        self.is_rowsfrom = obj.get('is_rowsfrom')
        self.functions = build_from_item(obj, 'functions')
        self.alias = build_from_item(obj, 'alias')
        self.coldeflist = build_from_item(obj, 'coldeflist')


class AArrayExpr(Node):

    def __init__(self, obj):
        self.elements = build_from_item(obj, 'elements')
        self.location = obj.get('location')


class AIndices(Node):
    def __init__(self, obj):
        self.lidx = build_from_item(obj, 'lidx')
        self.uidx = build_from_item(obj, 'uidx')


class MultiAssignRef(Node):

    def __init__(self, obj):
        self.source = build_from_item(obj, 'source')
        self.colno = obj.get('colno')
        self.ncolumns = obj.get('ncolumns')
