# -*- coding: utf-8 -*-
# :Project:   psqlparse -- Pretty Indent SQL
# :Created:   gio 27 lug 2017 08:39:28 CEST
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   BSD
# :Copyright: © 2017 Lele Gaifax
#

from contextlib import contextmanager
from inspect import isclass

from six import PY2, StringIO

from . import nodes, parse


NODE_PRINTERS = {}
"Registry of specialized printers."


def get_printer_for_node(node):
    "Get specific printer implementation for given `node` instance."

    try:
        return NODE_PRINTERS[type(node)]
    except KeyError:
        raise NotImplementedError("Printer for node %r is not implemented yet"
                                  % node.__class__.__name__)


def node_printer(node_class):
    "Decorator to register a specific printer implementation for given `node_class`."

    def decorator(impl):
        assert isclass(node_class)
        assert node_class not in NODE_PRINTERS
        NODE_PRINTERS[node_class] = impl
        return impl
    return decorator


class Serializer(StringIO, object):
    def __init__(self):
        super(Serializer, self).__init__()
        self.expression_level = 0

    if PY2:
        def write(self, s):
            super(Serializer, self).write(s)
            return len(s)

    def newline_and_indent(self):
        self.write(' ')

    def indent(self, amount=0):
        pass

    def dedent(self):
        pass

    @contextmanager
    def push_indent(self, amount=0):
        self.indent(amount)
        yield
        self.dedent()

    def print_node(self, node):
        printer = get_printer_for_node(node)
        printer(node, self)

    def _print_list_items(self, items, sep):
        first = True
        for item in items:
            if first:
                first = False
            else:
                self.newline_and_indent()
                self.write(sep)
            self.print_node(item)

    def print_list(self, items, sep=', ', relative_indent=None):
        if relative_indent is None:
            relative_indent = -len(sep)
        with self.push_indent(relative_indent):
            self._print_list_items(items, sep)

    def print_expression(self, items, operator):
        self.expression_level += 1
        if self.expression_level > 1:
            if self.align_expression_operands:
                oplen = len(operator)
                self.write('(' + ' '*oplen)
                indent = -oplen
            else:
                self.write('(')
                indent = 0
        else:
            indent = -len(operator)

        with self.push_indent(indent):
            self._print_list_items(items, operator)

        self.expression_level -= 1
        if self.expression_level > 0:
            self.write(')')

    def __call__(self, sql):
        first = True
        for statement in parse(sql):
            if first:
                first = False
            else:
                self.write(';')
                self.newline_and_indent()
                if self.separate_statements:
                    self.newline_and_indent()
            self.print_node(statement)
        return self.getvalue()


class PrettyPrinter(Serializer):
    def __init__(self,
                 align_expression_operands=True,
                 separate_statements=True):
        super(PrettyPrinter, self).__init__()
        self.align_expression_operands = align_expression_operands
        self.separate_statements = separate_statements
        self.column = 0
        self.current_indent = 0
        self.indentation_stack = []

    def write(self, s):
        count = super(PrettyPrinter, self).write(s)
        if s == '\n':
            self.column = 0
        else:
            self.column += count
        return count

    def indent(self, amount=0):
        self.indentation_stack.append(self.current_indent)
        self.current_indent = self.column + amount

    def dedent(self):
        self.current_indent = self.indentation_stack.pop()

    def newline_and_indent(self):
        self.write('\n')
        self.write(' ' * self.current_indent)


##
## Specific Node printers
##


@node_printer(nodes.AArrayExpr)
def a_array_expr(node, output):
    output.write('ARRAY[')
    output.print_list(node.elements)
    output.write(']')


@node_printer(nodes.AConst)
def a_const(node, output):
    output.print_node(node.val)


@node_printer(nodes.AExpr)
def a_expr(node, output):
    output.print_node(node.lexpr)
    for operator in node.name:
        output.write(' ')
        output.print_node(operator)
    output.write(' ')
    output.print_node(node.rexpr)


@node_printer(nodes.Alias)
def alias(node, output):
    output.print_node(node.aliasname)
    if node.colnames is not None:
        output.write(' (  ')
        output.print_list(node.colnames)
        output.write(')')


@node_printer(nodes.BoolExpr)
def bool_expr(node, output):
    operator = ('AND ', 'OR ')[node.boolop]
    output.print_expression(node.args, operator)


@node_printer(nodes.CaseExpr)
def case_expr(node, output):
    with output.push_indent():
        output.write('CASE')
        if node.arg is not None:
            output.write(' ')
            output.print_node(node.arg)
        output.newline_and_indent()
        output.write('  ')
        with output.push_indent():
            output.print_list(node.args, '')
            if node.def_result is not None:
                output.newline_and_indent()
                output.write('ELSE ')
                output.print_node(node.def_result)
        output.newline_and_indent()
        output.write('END')


@node_printer(nodes.CaseWhen)
def case_when(node, output):
    output.write('WHEN ')
    with output.push_indent(-3):
        output.print_node(node.expr)
        output.newline_and_indent()
        output.write('THEN ')
        output.print_node(node.result)


@node_printer(nodes.ColumnRef)
def column_ref(node, output):
    output.write('.'.join('*' if isinstance(c, nodes.AStar) else c.str
                          for c in node.fields))


@node_printer(nodes.CommonTableExpr)
def common_table_expr(node, output):
    output.print_node(node.ctename)
    if node.aliascolnames is not None:
        output.write('(')
        if len(node.aliascolnames) > 1:
            output.write('  ')
        output.print_list(node.aliascolnames)
        output.write(')')
        output.newline_and_indent()
    else:
        output.write(' ')
    output.write('AS (')
    output.print_node(node.ctequery)
    output.write(')')
    output.newline_and_indent()


@node_printer(nodes.DeleteStmt)
def delete_stmt(node, output):
    with output.push_indent():
        if node.with_clause is not None:
            output.write('WITH ')
            output.print_node(node.with_clause)
            output.newline_and_indent()

        output.write('DELETE FROM ')
        output.print_node(node.relation)
        if node.using_clause is not None:
            output.newline_and_indent()
            output.write('USING ')
            output.print_list(node.using_clause)
        if node.where_clause is not None:
            output.newline_and_indent()
            output.write(' WHERE ')
            output.print_node(node.where_clause)
        if node.returning_list is not None:
            output.newline_and_indent()
            output.write(' RETURNING ')
            output.print_list(node.returning_list)


@node_printer(nodes.Float)
def float(node, output):
    output.write(str(node))


@node_printer(nodes.FuncCall)
def func_call(node, output):
    output.write('.'.join(n.str for n in node.funcname))
    output.write('(')
    if node.agg_distinct:
        output.write('DISTINCT ')
    if node.args is None:
        if node.agg_star:
            output.write('*')
    else:
        if len(node.args) > 1:
            output.write('  ')
        output.print_list(node.args)
    if node.agg_order is not None:
        if node.agg_within_group is None:
            output.write(' ORDER BY ')
            output.print_list(node.agg_order)
        else:
            output.write(') WITHIN GROUP (ORDER BY ')
            output.print_list(node.agg_order)
    output.write(')')
    if node.agg_filter is not None:
        output.write(' FILTER (WHERE ')
        output.print_node(node.agg_filter)
        output.write(')')
    if node.over is not None:
        output.write(' OVER ')
        output.print_node(node.over)


@node_printer(nodes.Integer)
def integer(node, output):
    output.write(str(node))


@node_printer(nodes.JoinExpr)
def join_expr(node, output):
    with output.push_indent(-3):
        output.print_node(node.larg)
        output.newline_and_indent()
        if node.is_natural:
            output.write('NATURAL ')
        output.write(('INNER', 'LEFT', 'FULL', 'RIGHT')[node.jointype])
        output.write(' JOIN ')
        output.print_node(node.rarg)
        if node.using_clause is not None:
            output.write(' USING (')
            output.print_list(node.using_clause)
            output.write(')')
        elif node.quals is not None:
            output.write(' ON ')
            output.print_node(node.quals)
        if node.alias is not None:
            output.write(' AS ')
            output.print_node(node.alias)


@node_printer(nodes.Literal)
def literal(node, output):
    name = node.str
    if name == '~~':
        name = 'LIKE'
    output.write(name)


@node_printer(nodes.LockingClause)
def locking_clause(node, output):
    output.write((None,
                  'KEY SHARE',
                  'SHARE',
                  'NO KEY UPDATE',
                  'UPDATE')[node.strength])
    if node.locked_rels is not None:
        output.write(' OF ')
        output.print_list(node.locked_rels)
    if node.wait_policy:
        output.write(' ')
        output.write((None, 'SKIP LOCKED', 'NOWAIT')[node.wait_policy])


@node_printer(nodes.MultiAssignRef)
def multi_assign_ref(node, output):
    output.print_node(node.source)


@node_printer(nodes.Name)
def name(node, output):
    output.write(str(node))


@node_printer(nodes.NullTest)
def null_test(node, output):
    output.print_node(node.arg)
    output.write(' IS')
    if node.type == nodes.NullTest.TYPE_IS_NOT_NULL:
        output.write(' NOT')
    output.write(' NULL')


@node_printer(nodes.RangeFunction)
def range_function(node, output):
    if node.lateral:
        output.write('LATERAL ')
    for fun, cdefs in node.functions:
        output.print_node(fun)
        if cdefs is not None:
            output.write(' AS ')
            output.print_list(cdefs)
    if node.alias is not None:
        output.write(' AS ')
        output.print_node(node.alias)
    if node.ordinality:
        output.write(' WITH ORDINALITY')


@node_printer(nodes.RangeSubselect)
def range_subselect(node, output):
    if node.lateral:
        output.write('LATERAL ')
    output.print_node(node.subquery)
    if node.alias is not None:
        output.write(' AS ')
        output.print_node(node.alias)


@node_printer(nodes.RangeVar)
def range_var(node, output):
    if node.inh_opt == nodes.RangeVar.INH_NO:
        output.write('ONLY ')
    if node.schemaname:
        output.write(node.schemaname)
        output.write('.')
    output.write(node.relname)
    alias = node.alias
    if alias:
        output.write(' AS ')
        output.print_node(alias)


@node_printer(nodes.ResTarget)
def res_target(node, output):
    output.print_node(node.val)
    name = node.name
    if name:
        output.write(' AS ')
        output.print_node(name)


@node_printer(nodes.ResTargetUpdate)
def res_target_update(node, output):
    if isinstance(node.val, nodes.MultiAssignRef):
        if node.val.colno == 1:
            output.write('(  ')
            output.indent(-2)
        output.print_node(node.name)
        if node.val.colno == node.val.ncolumns:
            output.dedent()
            output.write(') = ')
            output.print_node(node.val)
    else:
        output.print_node(node.name)
        if node.indirection is not None:
            output.print_list(node.indirection)
        output.write(' = ')
        output.print_node(node.val)


@node_printer(nodes.SelectStmt)
def select_stmt(node, output):
    with output.push_indent():
        if node.with_clause is not None:
            output.write('WITH ')
            output.print_node(node.with_clause)
            output.newline_and_indent()

        if node.values_lists is not None:
            output.write('(VALUES (  ')
            with output.push_indent(-5):
                first = True
                for values in node.values_lists:
                    if first:
                        first = False
                    else:
                        output.newline_and_indent()
                        output.write(', (  ')
                    output.print_list(values)
                    output.write(')')
                output.write(')')
        elif node.target_list is None:
            with output.push_indent():
                output.print_node(node.larg)
                output.newline_and_indent()
                output.newline_and_indent()
                output.write((None, 'UNION', 'INTERSECT', 'EXCEPT')[node.op])
                if node.all:
                    output.write(' ALL')
                output.newline_and_indent()
                output.newline_and_indent()
                output.print_node(node.rarg)
        else:
            output.write('SELECT')
            if node.distinct_clause:
                output.write(' DISTINCT')
                if node.distinct_clause[0]:
                    output.write(' ON (')
                    output.print_list(node.distinct_clause)
                    output.write(')')
            output.write(' ')
            output.print_list(node.target_list)
            if node.from_clause is not None:
                output.newline_and_indent()
                output.write('FROM ')
                output.print_list(node.from_clause)
            if node.where_clause is not None:
                output.newline_and_indent()
                output.write('WHERE ')
                output.print_node(node.where_clause)
            if node.group_clause is not None:
                output.newline_and_indent()
                output.write('GROUP BY ')
                output.print_list(node.group_clause)
            if node.having_clause is not None:
                output.newline_and_indent()
                output.write('HAVING ')
                output.print_node(node.having_clause)
            if node.window_clause is not None:
                output.newline_and_indent()
                output.write('WINDOW ')
                output.print_list(node.window_clause)
            if node.sort_clause is not None:
                output.newline_and_indent()
                output.write('ORDER BY ')
                output.print_list(node.sort_clause)
            if node.limit_count is not None:
                output.newline_and_indent()
                output.write('LIMIT ')
                output.print_node(node.limit_count)
            if node.limit_offset is not None:
                output.newline_and_indent()
                output.write('OFFSET ')
                output.print_node(node.limit_offset)
            if node.locking_clause is not None:
                output.newline_and_indent()
                output.write('FOR ')
                output.print_list(node.locking_clause)


@node_printer(nodes.SetToDefault)
def set_to_default(node, output):
    output.write('DEFAULT')


@node_printer(nodes.SortBy)
def sort_by(node, output):
    output.print_node(node.node)
    if node.dir == nodes.SortBy.DIR_ASC:
        output.write(' ASC')
    elif node.dir == nodes.SortBy.DIR_DESC:
        output.write(' DESC')
    elif node.dir == nodes.SortBy.DIR_USING:
        output.write(' USING ')
        output.print_list(node.using)
    if node.nulls:
        output.write(' NULLS ')
        output.write('FIRST' if node.nulls == nodes.SortBy.NULLS_FIRST else 'LAST')


@node_printer(nodes.String)
def string(node, output):
    output.write("'%s'" % node)


@node_printer(nodes.SubLink)
def sub_link(node, output):
    output.write('(')
    with output.push_indent():
        output.print_node(node.subselect)
    output.write(')')


_common_values = {
    't::pg_catalog.bool': 'TRUE',
    'f::pg_catalog.bool': 'FALSE',
    'now::pg_catalog.text::pg_catalog.date': 'CURRENT_DATE',
}

@node_printer(nodes.TypeCast)
def type_cast(node, output):
    # Replace common values
    if isinstance(node.arg, nodes.TypeCast):
        if isinstance(node.arg.arg, nodes.AConst):
            value = '%s::%s::%s' % (
                node.arg.arg.val,
                ('.'.join(str(n) for n in node.arg.type_name.names)),
                ('.'.join(str(n) for n in node.type_name.names)))
            if value in _common_values:
                output.write(_common_values[value])
                return
    elif isinstance(node.arg, nodes.AConst):
        value = '%s::%s' % (
            node.arg.val,
            ('.'.join(str(n) for n in node.type_name.names)))
        if value in _common_values:
            output.write(_common_values[value])
            return
    output.print_node(node.arg)
    output.write('::')
    output.print_node(node.type_name)


@node_printer(nodes.TypeName)
def type_name(node, output):
    names = node.names
    output.write('.'.join(str(n) for n in names))


@node_printer(nodes.UpdateStmt)
def update_stmt(node, output):
    with output.push_indent():
        if node.with_clause is not None:
            output.write('WITH ')
            output.print_node(node.with_clause)
            output.newline_and_indent()

        output.write('UPDATE ')
        output.print_node(node.relation)
        output.newline_and_indent()
        output.write('   SET ')
        output.print_list(node.target_list)
        if node.from_clause is not None:
            output.newline_and_indent()
            output.write('  FROM ')
            output.print_list(node.from_clause)
        if node.where_clause is not None:
            output.newline_and_indent()
            output.write(' WHERE ')
            output.print_node(node.where_clause)
        if node.returning_list is not None:
            output.newline_and_indent()
            output.write(' RETURNING ')
            output.print_list(node.returning_list)


@node_printer(nodes.WindowDef)
def window_def(node, output):
    empty = node.partition_clause is None and node.order_clause is None
    if node.name is not None:
        output.print_node(node.name)
        if not empty:
            output.write(' AS ')
    if not empty or node.name is None:
        output.write('(')
        with output.push_indent():
            if node.partition_clause is not None:
                output.write('PARTITION BY ')
                output.print_list(node.partition_clause)
            if node.order_clause is not None:
                if node.partition_clause is not None:
                    output.newline_and_indent()
                output.write('ORDER BY ')
                output.print_list(node.order_clause)
        output.write(')')


@node_printer(nodes.WithClause)
def with_clause(node, output):
    relindent = -3
    if node.recursive:
        relindent -= output.write('RECURSIVE ')
    output.print_list(node.ctes, relative_indent=relindent)
