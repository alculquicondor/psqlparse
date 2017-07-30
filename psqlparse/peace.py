# -*- coding: utf-8 -*-
# :Project:   psqlparse -- Pretty Indent SQL
# :Created:   gio 27 lug 2017 08:39:28 CEST
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   BSD
# :Copyright: © 2017 Lele Gaifax
#

from contextlib import contextmanager
from inspect import isclass

from six import io

from . import nodes, parse


class Serializer(io.StringIO):
    def __init__(self):
        super().__init__()
        self.expression_level = 0

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
        NodePrinter.get(node)(self)

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
        super().__init__()
        self.align_expression_operands = align_expression_operands
        self.separate_statements = separate_statements
        self.column = 0
        self.current_indent = 0
        self.indentation_stack = []

    def write(self, s):
        count = super().write(s)
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

    # def print_list(self, items, sep=', '):
    #     suboutput = Serializer()
    #     suboutput.print_list(items, sep)
    #     result = suboutput.getvalue()
    #     if self.column + len(result) < 80:
    #         self.write(result)
    #         self.newline_and_indent()
    #     else:
    #         with self.push_indent(-len(sep)):
    #             self._print_list_items(items, sep)


class NodePrinter:
    IMPL_FOR_NODE_CLASS = {}

    def __init__(self, node):
        self.node = node

    def __call__(self, output):
        raise NotImplementedError

    @classmethod
    def get(cls, node):
        try:
            return cls.IMPL_FOR_NODE_CLASS[type(node)](node)
        except KeyError:
            if isinstance(node, dict):
                from pprint import pprint
                pprint(node)
            raise


def node_printer(node_class):
    def decorator(impl):
        if isclass(impl):
            printer_class = impl
        else:
            printer_class = type(node_class.__name__, (NodePrinter,),
                                 {'__call__': impl})
        NodePrinter.IMPL_FOR_NODE_CLASS[node_class] = printer_class
        return printer_class
    return decorator


@node_printer(nodes.AArrayExpr)
def a_array_expr(self, output):
    output.write('ARRAY[')
    output.print_list(self.node.elements)
    output.write(']')


@node_printer(nodes.AConst)
def a_const(self, output):
    output.print_node(self.node.val)


@node_printer(nodes.AExpr)
def a_expr(self, output):
    output.print_node(self.node.lexpr)
    for operator in self.node.name:
        output.write(' ')
        output.print_node(operator)
    output.write(' ')
    output.print_node(self.node.rexpr)


@node_printer(nodes.Alias)
def alias(self, output):
    output.print_node(self.node.aliasname)
    if self.node.colnames is not None:
        output.write(' (  ')
        output.print_list(self.node.colnames)
        output.write(')')


@node_printer(nodes.BoolExpr)
def bool_expr(self, output):
    operator = ('AND ', 'OR ')[self.node.boolop]
    output.print_expression(self.node.args, operator)


@node_printer(nodes.CaseExpr)
def case_expr(self, output):
    with output.push_indent():
        output.write('CASE')
        if self.node.arg is not None:
            output.write(' ')
            output.print_node(self.node.arg)
        output.newline_and_indent()
        output.write('  ')
        with output.push_indent():
            output.print_list(self.node.args, '')
            if self.node.def_result is not None:
                output.newline_and_indent()
                output.write('ELSE ')
                output.print_node(self.node.def_result)
        output.newline_and_indent()
        output.write('END')


@node_printer(nodes.CaseWhen)
def case_when(self, output):
    output.write('WHEN ')
    with output.push_indent(-3):
        output.print_node(self.node.expr)
        output.newline_and_indent()
        output.write('THEN ')
        output.print_node(self.node.result)


@node_printer(nodes.ColumnRef)
def column_ref(self, output):
    output.write('.'.join('*' if isinstance(c, nodes.AStar) else c.str
                          for c in self.node.fields))


@node_printer(nodes.CommonTableExpr)
def common_table_expr(self, output):
    output.print_node(self.node.ctename)
    if self.node.aliascolnames is not None:
        output.write('(')
        if len(self.node.aliascolnames) > 1:
            output.write('  ')
        output.print_list(self.node.aliascolnames)
        output.write(')')
        output.newline_and_indent()
    else:
        output.write(' ')
    output.write('AS (')
    output.print_node(self.node.ctequery)
    output.write(')')
    output.newline_and_indent()


@node_printer(nodes.Float)
def float(self, output):
    output.write(str(self.node))


@node_printer(nodes.FuncCall)
def func_call(self, output):
    output.write('.'.join(n.str for n in self.node.funcname))
    output.write('(')
    if self.node.agg_distinct:
        output.write('DISTINCT ')
    if self.node.args is None:
        if self.node.agg_star:
            output.write('*')
    else:
        if len(self.node.args) > 1:
            output.write('  ')
        output.print_list(self.node.args)
    if self.node.agg_order is not None:
        if self.node.agg_within_group is None:
            output.write(' ORDER BY ')
            output.print_list(self.node.agg_order)
        else:
            output.write(') WITHIN GROUP (ORDER BY ')
            output.print_list(self.node.agg_order)
    output.write(')')
    if self.node.agg_filter is not None:
        output.write(' FILTER (WHERE ')
        output.print_node(self.node.agg_filter)
        output.write(')')
    if self.node.over is not None:
        output.write(' OVER ')
        output.print_node(self.node.over)


@node_printer(nodes.Integer)
def integer(self, output):
    output.write(str(self.node))


@node_printer(nodes.JoinExpr)
def join_expr(self, output):
    with output.push_indent(-3):
        output.print_node(self.node.larg)
        output.newline_and_indent()
        if self.node.is_natural:
            output.write('NATURAL ')
        output.write(('INNER', 'LEFT', 'FULL', 'RIGHT')[self.node.jointype])
        output.write(' JOIN ')
        output.print_node(self.node.rarg)
        if self.node.using_clause is not None:
            output.write(' USING (')
            output.print_list(self.node.using_clause)
            output.write(')')
        elif self.node.quals is not None:
            output.write(' ON ')
            output.print_node(self.node.quals)
        if self.node.alias is not None:
            output.write(' AS ')
            output.print_node(self.node.alias)


@node_printer(nodes.Literal)
def literal(self, output):
    name = self.node.str
    if name == '~~':
        name = 'LIKE'
    output.write(name)


@node_printer(nodes.LockingClause)
def locking_clause(self, output):
    output.write((None,
                  'KEY SHARE',
                  'SHARE',
                  'NO KEY UPDATE',
                  'UPDATE')[self.node.strength])
    if self.node.locked_rels is not None:
        output.write(' OF ')
        output.print_list(self.node.locked_rels)
    if self.node.wait_policy:
        output.write(' ')
        output.write((None, 'SKIP LOCKED', 'NOWAIT')[self.node.wait_policy])


@node_printer(nodes.MultiAssignRef)
def multi_assign_ref(self, output):
    output.print_node(self.node.source)


@node_printer(nodes.Name)
def name(self, output):
    output.write(str(self.node))


@node_printer(nodes.NullTest)
def null_test(self, output):
    output.print_node(self.node.arg)
    output.write(' IS')
    if self.node.type == nodes.NullTest.TYPE_IS_NOT_NULL:
        output.write(' NOT')
    output.write(' NULL')


@node_printer(nodes.RangeFunction)
def range_function(self, output):
    if self.node.lateral:
        output.write('LATERAL ')
    for fun, cdefs in self.node.functions:
        output.print_node(fun)
        if cdefs is not None:
            output.write(' AS ')
            output.print_list(cdefs)
    if self.node.alias is not None:
        output.write(' AS ')
        output.print_node(self.node.alias)
    if self.node.ordinality:
        output.write(' WITH ORDINALITY')


@node_printer(nodes.RangeSubselect)
def range_subselect(self, output):
    if self.node.lateral:
        output.write('LATERAL ')
    output.print_node(self.node.subquery)
    if self.node.alias is not None:
        output.write(' AS ')
        output.print_node(self.node.alias)


@node_printer(nodes.RangeVar)
def range_var(self, output):
    if self.node.schemaname:
        output.write(self.node.schemaname)
        output.write('.')
    output.write(self.node.relname)
    alias = self.node.alias
    if alias:
        output.write(' AS ')
        output.print_node(alias)


@node_printer(nodes.ResTarget)
def res_target(self, output):
    output.print_node(self.node.val)
    name = self.node.name
    if name:
        output.write(' AS ')
        output.print_node(name)


@node_printer(nodes.ResTargetUpdate)
def res_target_update(self, output):
    if isinstance(self.node.val, nodes.MultiAssignRef):
        if self.node.val.colno == 1:
            output.write('(  ')
            output.indent(-2)
        output.print_node(self.node.name)
        if self.node.val.colno == self.node.val.ncolumns:
            output.dedent()
            output.write(') = ')
            output.print_node(self.node.val)
    else:
        output.print_node(self.node.name)
        if self.node.indirection is not None:
            output.print_list(self.node.indirection)
        output.write(' = ')
        output.print_node(self.node.val)


@node_printer(nodes.SelectStmt)
def select_stmt(self, output):
    with output.push_indent():
        if self.node.with_clause is not None:
            output.write('WITH ')
            output.print_node(self.node.with_clause)
            output.newline_and_indent()

        if self.node.values_lists is not None:
            output.write('(VALUES (  ')
            with output.push_indent(-5):
                first = True
                for values in self.node.values_lists:
                    if first:
                        first = False
                    else:
                        output.newline_and_indent()
                        output.write(', (  ')
                    output.print_list(values)
                    output.write(')')
                output.write(')')
        elif self.node.target_list is None:
            with output.push_indent():
                output.print_node(self.node.larg)
                output.newline_and_indent()
                output.newline_and_indent()
                output.write((None, 'UNION', 'INTERSECT', 'EXCEPT')[self.node.op])
                if self.node.all:
                    output.write(' ALL')
                output.newline_and_indent()
                output.newline_and_indent()
                output.print_node(self.node.rarg)
        else:
            output.write('SELECT')
            if self.node.distinct_clause:
                output.write(' DISTINCT')
                if self.node.distinct_clause[0]:
                    output.write(' ON (')
                    output.print_list(self.node.distinct_clause)
                    output.write(')')
            output.write(' ')
            output.print_list(self.node.target_list)
            if self.node.from_clause is not None:
                output.newline_and_indent()
                output.write('FROM ')
                output.print_list(self.node.from_clause)
            if self.node.where_clause is not None:
                output.newline_and_indent()
                output.write('WHERE ')
                output.print_node(self.node.where_clause)
            if self.node.group_clause is not None:
                output.newline_and_indent()
                output.write('GROUP BY ')
                output.print_list(self.node.group_clause)
            if self.node.having_clause is not None:
                output.newline_and_indent()
                output.write('HAVING ')
                output.print_node(self.node.having_clause)
            if self.node.window_clause is not None:
                output.newline_and_indent()
                output.write('WINDOW ')
                output.print_list(self.node.window_clause)
            if self.node.sort_clause is not None:
                output.newline_and_indent()
                output.write('ORDER BY ')
                output.print_list(self.node.sort_clause)
            if self.node.limit_count is not None:
                output.newline_and_indent()
                output.write('LIMIT ')
                output.print_node(self.node.limit_count)
            if self.node.limit_offset is not None:
                output.newline_and_indent()
                output.write('OFFSET ')
                output.print_node(self.node.limit_offset)
            if self.node.locking_clause is not None:
                output.newline_and_indent()
                output.write('FOR ')
                output.print_list(self.node.locking_clause)


@node_printer(nodes.SetToDefault)
def set_to_default(self, output):
    output.write('DEFAULT')


@node_printer(nodes.SortBy)
def sort_by(self, output):
    output.print_node(self.node.node)
    if self.node.dir == nodes.SortBy.DIR_ASC:
        output.write(' ASC')
    elif self.node.dir == nodes.SortBy.DIR_DESC:
        output.write(' DESC')
    elif self.node.dir == nodes.SortBy.DIR_USING:
        output.write(' USING ')
        output.print_list(self.node.using)
    if self.node.nulls:
        output.write(' NULLS ')
        output.write('FIRST' if self.node.nulls == nodes.SortBy.NULLS_FIRST else 'LAST')


@node_printer(nodes.String)
def string(self, output):
    output.write("'%s'" % self.node)


@node_printer(nodes.SubLink)
def sub_link(self, output):
    output.write('(')
    with output.push_indent():
        output.print_node(self.node.subselect)
    output.write(')')


_common_values = {
    't::pg_catalog.bool': 'TRUE',
    'f::pg_catalog.bool': 'FALSE',
    'now::pg_catalog.text::pg_catalog.date': 'CURRENT_DATE',
}

@node_printer(nodes.TypeCast)
def type_cast(self, output):
    # Replace common values
    if isinstance(self.node.arg, nodes.TypeCast):
        if isinstance(self.node.arg.arg, nodes.AConst):
            value = '%s::%s::%s' % (
                self.node.arg.arg.val,
                ('.'.join(str(n) for n in self.node.arg.type_name.names)),
                ('.'.join(str(n) for n in self.node.type_name.names)))
            if value in _common_values:
                output.write(_common_values[value])
                return
    elif isinstance(self.node.arg, nodes.AConst):
        value = '%s::%s' % (
            self.node.arg.val,
            ('.'.join(str(n) for n in self.node.type_name.names)))
        if value in _common_values:
            output.write(_common_values[value])
            return
    output.print_node(self.node.arg)
    output.write('::')
    output.print_node(self.node.type_name)


@node_printer(nodes.TypeName)
def type_name(self, output):
    names = self.node.names
    output.write('.'.join(str(n) for n in names))


@node_printer(nodes.UpdateStmt)
def update_stmt(self, output):
    with output.push_indent():
        if self.node.with_clause is not None:
            output.write('WITH ')
            output.print_node(self.node.with_clause)
            output.newline_and_indent()

        output.write('UPDATE ')
        output.print_node(self.node.relation)
        output.newline_and_indent()
        output.write('   SET ')
        output.print_list(self.node.target_list)
        if self.node.from_clause is not None:
            output.newline_and_indent()
            output.write('  FROM ')
            output.print_list(self.node.from_clause)
        if self.node.where_clause is not None:
            output.newline_and_indent()
            output.write(' WHERE ')
            output.print_node(self.node.where_clause)
        if self.node.returning_list is not None:
            output.newline_and_indent()
            output.write(' RETURNING ')
            output.print_list(self.node.returning_list)


@node_printer(nodes.WindowDef)
def window_def(self, output):
    empty = self.node.partition_clause is None and self.node.order_clause is None
    if self.node.name is not None:
        output.print_node(self.node.name)
        if not empty:
            output.write(' AS ')
    if not empty or self.node.name is None:
        output.write('(')
        with output.push_indent():
            if self.node.partition_clause is not None:
                output.write('PARTITION BY ')
                output.print_list(self.node.partition_clause)
            if self.node.order_clause is not None:
                if self.node.partition_clause is not None:
                    output.newline_and_indent()
                output.write('ORDER BY ')
                output.print_list(self.node.order_clause)
        output.write(')')


@node_printer(nodes.WithClause)
def with_clause(self, output):
    relindent = -3
    if self.node.recursive:
        relindent -= output.write('RECURSIVE ')
    output.print_list(self.node.ctes, relative_indent=relindent)
