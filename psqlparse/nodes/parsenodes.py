import six

from .utils import build_from_item
from .nodes import Node
from .value import Name

# See https://github.com/postgres/postgres/blob/master/src/include/nodes/parsenodes.h


class Statement(Node):

    statement = ''

    def __str__(self):
        return self.statement


class SelectStmt(Statement):

    OP_NONE = 0
    OP_UNION = 1
    OP_INTERSECT = 2
    OP_EXCEPT = 3

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
        self.target_list = build_from_item(obj, 'targetList', 'ResTargetUpdate')
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
        self.ctename = Name.from_string(obj.get('ctename'))
        self.aliascolnames = build_from_item(obj, 'aliascolnames', 'Name')
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
        self.name = Name.from_string(obj.get('name'))
        self.indirection = build_from_item(obj, 'indirection')
        self.val = build_from_item(obj, 'val')
        self.location = obj.get('location')

    def tables(self):
        return set()


class ResTargetUpdate(ResTarget):
    "The UPDATE specific variant."


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
        return set()


class AStar(Node):

    def __init__(self, obj):
        pass

    def tables(self):
        return set()


class AExpr(Node):

    KIND_OP = 0                 # normal operator
    KIND_OP_ANY = 1             # scalar op ANY (array)
    KIND_OP_ALL = 2             # scalar op ALL (array)
    KIND_DISTINCT = 3           # IS DISTINCT FROM - name must be "="
    KIND_NOT_DISTINCT = 4       # IS NOT DISTINCT FROM - name must be "="
    KIND_NULLIF = 5             # NULLIF - name must be "="
    KIND_OF = 6                 # IS [NOT] OF - name must be "=" or "<>"
    KIND_IN = 7                 # [NOT] IN - name must be "=" or "<>"
    KIND_LIKE = 8               # [NOT] LIKE - name must be "~~" or "!~~"
    KIND_ILIKE = 9              # [NOT] ILIKE - name must be "~~*" or "!~~*"
    KIND_SIMILAR = 10           # [NOT] SIMILAR - name must be "~" or "!~"
    KIND_BETWEEN = 11           # name must be "BETWEEN"
    KIND_NOT_BETWEEN = 12       # name must be "NOT BETWEEN"
    KIND_BETWEEN_SYM = 13       # name must be "BETWEEN SYMMETRIC"
    KIND_NOT_BETWEEN_SYM = 14   # name must be "NOT BETWEEN SYMMETRIC"
    KIND_PAREN = 15             # nameless dummy node for parentheses

    def __init__(self, obj):
        self.kind = obj.get('kind')
        self.name = build_from_item(obj, 'name', 'Literal')
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

    def tables(self):
        return set()


class TypeName(Node):
    def __init__(self, obj):
        self.names = build_from_item(obj, 'names')
        self.setof = obj.get('setof')
        self.pct_type = obj.get('pct_type')
        self.type_mods = build_from_item(obj, 'typmods')
        self.type_mod = obj.get('typemod')
        self.array_bounds = build_from_item(obj, 'arrayBounds')
        self.location = obj.get('location')

    def tables(self):
        return set()


class SortBy(Node):
    DIR_DEFAULT = 0
    DIR_ASC = 1
    DIR_DESC = 2
    DIR_USING = 3

    NULLS_DEFAULT = 0
    NULLS_FIRST = 1
    NULLS_LAST = 2

    def __init__(self, obj):
        self.node = build_from_item(obj, 'node')
        self.dir = obj.get('sortby_dir')
        self.nulls = obj.get('sortby_nulls')
        self.using = build_from_item(obj, 'useOp', 'Literal')
        self.location = obj.get('location')

    def tables(self):
        return set()


class WindowDef(Node):
    FRAME_NONDEFAULT = 0x00001                #  any specified?
    FRAME_RANGE = 0x00002                     #  RANGE behavior
    FRAME_ROWS = 0x00004                      #  ROWS behavior
    FRAME_BETWEEN = 0x00008                   #  BETWEEN given?
    FRAME_START_UNBOUNDED_PRECEDING = 0x00010 #  start is U. P.
    FRAME_END_UNBOUNDED_PRECEDING = 0x00020   #  (disallowed)
    FRAME_START_UNBOUNDED_FOLLOWING = 0x00040 #  (disallowed)
    FRAME_END_UNBOUNDED_FOLLOWING = 0x00080   #  end is U. F.
    FRAME_START_CURRENT_ROW = 0x00100         #  start is C. R.
    FRAME_END_CURRENT_ROW = 0x00200           #  end is C. R.
    FRAME_START_VALUE_PRECEDING = 0x00400     #  start is V. P.
    FRAME_END_VALUE_PRECEDING = 0x00800       #  end is V. P.
    FRAME_START_VALUE_FOLLOWING = 0x01000     #  start is V. F.
    FRAME_END_VALUE_FOLLOWING = 0x02000       #  end is V. F.

    FRAME_START_VALUE = (FRAME_START_VALUE_PRECEDING
                         | FRAME_START_VALUE_FOLLOWING)
    FRAME_END_VALUE = (FRAME_END_VALUE_PRECEDING
                       | FRAME_END_VALUE_FOLLOWING)
    FRAME_DEFAULTS = (FRAME_RANGE
                      | FRAME_START_UNBOUNDED_PRECEDING
                      | FRAME_END_CURRENT_ROW)

    def __init__(self, obj):
        self.name = Name.from_string(obj.get('name'))
        self.refname = Name.from_string(obj.get('refname'))
        self.partition_clause = build_from_item(obj, 'partitionClause')
        self.order_clause = build_from_item(obj, 'orderClause')
        self.frame_options = obj.get('frameOptions')
        self.start_offset = build_from_item(obj, 'startOffset')
        self.end_offset = build_from_item(obj, 'endOffset')
        self.location = obj.get('location')

    def tables(self):
        return set()


class LockingClause(Node):
    STRENGTH_NONE = 0           #  no such clause - only used in PlanRowMark
    STRENGTH_FORKEYSHARE = 1    #  FOR KEY SHARE
    STRENGTH_FORSHARE = 2       #  FOR SHARE
    STRENGTH_FORNOKEYUPDATE = 3 #  FOR NO KEY UPDATE
    STRENGTH_FORUPDATE = 4      #  FOR UPDATE

    WAIT_POLICY_BLOCK = 0       #  Wait for the lock to become available (default behavior)
    WAIT_POLICY_SKIP = 1        #  Skip rows that can't be locked (SKIP LOCKED)
    WAIT_POLICY_ERROR = 2       #  Raise an error if a row cannot be locked (NOWAIT)

    def __init__(self, obj):
        self.locked_rels = build_from_item(obj, 'lockedRels')
        self.strength = build_from_item(obj, 'strength')
        self.wait_policy = obj.get('waitPolicy')
        self.location = obj.get('location')

    def tables(self):
        return set()


class CaseExpr(Node):
    def __init__(self, obj):
        self.arg = build_from_item(obj, 'arg')
        self.args = build_from_item(obj, 'args')
        self.def_result = build_from_item(obj, 'defresult')
        self.location = obj.get('location')

    def tables(self):
        return set()


class CaseWhen(Node):
    def __init__(self, obj):
        self.expr = build_from_item(obj, 'expr')
        self.result = build_from_item(obj, 'result')
        self.location = obj.get('location')

    def tables(self):
        return set()


class NullTest(Node):
    TYPE_IS_NULL = 0
    TYPE_IS_NOT_NULL = 1

    def __init__(self, obj):
        self.arg = build_from_item(obj, 'arg')
        self.type = obj.get('nulltesttype')
        self.location = obj.get('location')

    def tables(self):
        return set()


class RangeFunction(Node):
    def __init__(self, obj):
        self.lateral = obj.get('lateral')
        self.ordinality = obj.get('ordinality')
        self.is_rowsfrom = obj.get('is_rowsfrom')
        self.functions = build_from_item(obj, 'functions')
        self.alias = build_from_item(obj, 'alias')
        self.col_defs = build_from_item(obj, 'coldeflist')
        self.location = obj.get('location')

    def tables(self):
        return set()


class AArrayExpr(Node):
    def __init__(self, obj):
        self.elements = build_from_item(obj, 'elements')
        self.location = obj.get('location')

    def tables(self):
        return set()


class MultiAssignRef(Node):
    def __init__(self, obj):
        self.source = build_from_item(obj, 'source')
        self.colno = obj.get('colno')
        self.ncolumns = obj.get('ncolumns')

    def tables(self):
        return set()


class AIndices(Node):
    def __init__(self, obj):
        # NB: this has been added in 9.6, see
        # https://github.com/postgres/postgres/blob/REL9_6_STABLE/src/include/nodes/parsenodes.h#L364
        self.is_slice = obj.get('is_slice')
        self.lidx = build_from_item(obj, 'lidx')
        self.uidx = build_from_item(obj, 'uidx')

    def tables(self):
        return set()
