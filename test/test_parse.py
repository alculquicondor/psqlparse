import unittest

from psqlparse import parse
from psqlparse.exceptions import PSqlParseError
from psqlparse import nodes


class SelectQueriesTest(unittest.TestCase):

    def test_select_all_no_where(self):
        query = "SELECT * FROM my_table"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertIsNone(stmt.where_clause)

        self.assertEqual(len(stmt.target_list), 1)
        target = stmt.target_list[0]
        self.assertIsInstance(target, nodes.ResTarget)
        self.assertIsInstance(target.val.fields[0], nodes.AStar)

        self.assertEqual(len(stmt.from_clause), 1)
        from_clause = stmt.from_clause[0]
        self.assertIsInstance(from_clause, nodes.RangeVar)
        self.assertEqual(from_clause.relname, 'my_table')

    def test_select_one_column_where(self):
        query = ("SELECT col1 FROM my_table "
                 "WHERE my_attribute LIKE 'condition'"
                 " AND other = 5.6 AND extra > 5")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertEqual(len(stmt.target_list), 1)
        target = stmt.target_list[0]
        self.assertIsInstance(target, nodes.ResTarget)
        self.assertEqual(target.val.fields[0].val, 'col1')

        self.assertIsInstance(stmt.where_clause, nodes.BoolExpr)
        self.assertEqual(len(stmt.where_clause.args), 3)

        one = stmt.where_clause.args[0]
        self.assertIsInstance(one, nodes.AExpr)
        self.assertEqual(str(one.lexpr.fields[0].val), 'my_attribute')
        self.assertEqual(str(one.name[0]), '~~')
        self.assertEqual(str(one.rexpr.val), 'condition')

        two = stmt.where_clause.args[1]
        self.assertIsInstance(two, nodes.AExpr)
        self.assertEqual(str(two.lexpr.fields[0].val), 'other')
        self.assertEqual(str(two.name[0]), '=')
        self.assertEqual(float(two.rexpr.val), 5.6)

        three = stmt.where_clause.args[2]
        self.assertIsInstance(three, nodes.AExpr)
        self.assertEqual(str(three.lexpr.fields[0].val), 'extra')
        self.assertEqual(str(three.name[0]), '>')
        self.assertEqual(int(three.rexpr.val), 5)

    def test_select_join(self):
        query = "SELECT * FROM table_one JOIN table_two USING (common)"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertEqual(len(stmt.from_clause), 1)
        join_expr = stmt.from_clause[0]
        self.assertIsInstance(join_expr, nodes.JoinExpr)

        self.assertIsInstance(join_expr.larg, nodes.RangeVar)
        self.assertEqual(join_expr.larg.relname, 'table_one')

        self.assertIsInstance(join_expr.rarg, nodes.RangeVar)
        self.assertEqual(join_expr.rarg.relname, 'table_two')

    def test_select_with(self):
        query = ("WITH fake_table AS (SELECT SUM(countable) AS total "
                 "FROM inner_table GROUP BY groupable) "
                 "SELECT * FROM fake_table")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertIsInstance(stmt.with_clause, nodes.WithClause)
        self.assertEqual(len(stmt.with_clause.ctes), 1)
        self.assertIsNone(stmt.with_clause.recursive)

        with_query = stmt.with_clause.ctes[0]
        self.assertEqual(with_query.ctename, 'fake_table')
        self.assertIsInstance(with_query.ctequery, nodes.SelectStmt)

    def test_select_subquery(self):
        query = "SELECT * FROM (SELECT something FROM dataset) AS other"
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.from_clause), 1)
        sub_query = stmt.from_clause[0]
        self.assertIsInstance(sub_query, nodes.RangeSubselect)
        self.assertIsInstance(sub_query.alias, nodes.Alias)
        self.assertEqual(sub_query.alias.aliasname, 'other')
        self.assertIsInstance(sub_query.subquery, nodes.SelectStmt)

        self.assertEqual(len(stmt.target_list), 1)

    def test_select_from_values(self):
        query = ("SELECT * FROM "
                 "(VALUES (1, 'one'), (2, 'two')) AS t (num, letter)")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertEqual(len(stmt.from_clause), 1)
        self.assertIsInstance(stmt.from_clause[0], nodes.RangeSubselect)

        alias = stmt.from_clause[0].alias
        self.assertIsInstance(alias, nodes.Alias)
        self.assertEqual(alias.aliasname, 't')
        self.assertEqual(['num', 'letter'], [str(v) for v in alias.colnames])

        subquery = stmt.from_clause[0].subquery
        self.assertIsInstance(subquery, nodes.SelectStmt)
        self.assertEqual(len(subquery.values_lists), 2)
        self.assertEqual([1, 'one'], [v.val.val
                                      for v in subquery.values_lists[0]])

    def test_select_case(self):
        query = ("SELECT a, CASE WHEN a=1 THEN 'one' WHEN a=2 THEN 'two'"
                 " ELSE 'other' END FROM test")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 2)
        target = stmt.target_list[1]
        self.assertIsInstance(target.val, nodes.CaseExpr)
        self.assertIsNone(target.val.arg)
        self.assertEqual(len(target.val.args), 2)
        self.assertIsInstance(target.val.args[0], nodes.CaseWhen)
        self.assertIsInstance(target.val.args[0].expr, nodes.AExpr)
        self.assertIsInstance(target.val.args[0].result, nodes.AConst)
        self.assertIsInstance(target.val.defresult, nodes.AConst)

        query = ("SELECT CASE a.value WHEN 0 THEN '1' ELSE '2' END FROM "
                 "sometable a")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 1)
        target = stmt.target_list[0]
        self.assertIsInstance(target.val, nodes.CaseExpr)
        self.assertIsInstance(target.val.arg, nodes.ColumnRef)

    def test_select_union(self):
        query = "SELECT * FROM table_one UNION select * FROM table_two"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertIsInstance(stmt.larg, nodes.SelectStmt)
        self.assertIsInstance(stmt.rarg, nodes.SelectStmt)

    def test_function_call(self):
        query = "SELECT * FROM my_table WHERE ST_Intersects(geo1, geo2)"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        func_call = stmt.where_clause
        self.assertIsInstance(func_call, nodes.FuncCall)
        self.assertEqual(str(func_call.funcname[0]), 'st_intersects')
        self.assertEqual(str(func_call.args[0].fields[0]), 'geo1')
        self.assertEqual(str(func_call.args[1].fields[0]), 'geo2')

    def test_select_type_cast(self):
        query = "SELECT 'accbf276-705b-11e7-b8e4-0242ac120002'::UUID"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 1)
        target = stmt.target_list[0]
        self.assertIsInstance(target, nodes.ResTarget)
        self.assertIsInstance(target.val, nodes.TypeCast)
        self.assertIsInstance(target.val.arg, nodes.AConst)
        self.assertEqual(target.val.arg.val.val,
                         'accbf276-705b-11e7-b8e4-0242ac120002')
        self.assertIsInstance(target.val.type_name, nodes.TypeName)
        self.assertEqual(target.val.type_name.names[0].val, "uuid")

    def test_select_order_by(self):
        query = "SELECT * FROM my_table ORDER BY field DESC NULLS FIRST"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.sort_clause), 1)
        self.assertIsInstance(stmt.sort_clause[0], nodes.SortBy)
        self.assertIsInstance(stmt.sort_clause[0].node, nodes.ColumnRef)
        self.assertEqual(stmt.sort_clause[0].sortby_dir, 2)
        self.assertEqual(stmt.sort_clause[0].sortby_nulls, 1)

        query = "SELECT * FROM my_table ORDER BY field USING @>"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt.sort_clause[0], nodes.SortBy)
        self.assertIsInstance(stmt.sort_clause[0].node, nodes.ColumnRef)
        self.assertEqual(len(stmt.sort_clause[0].use_op), 1)
        self.assertIsInstance(stmt.sort_clause[0].use_op[0], nodes.String)
        self.assertEqual(stmt.sort_clause[0].use_op[0].val, '@>')

    def test_select_window(self):
        query = "SELECT salary, sum(salary) OVER () FROM empsalary"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 2)
        target = stmt.target_list[1]
        self.assertIsInstance(target.val, nodes.FuncCall)
        self.assertIsInstance(target.val.over, nodes.WindowDef)
        self.assertIsNone(target.val.over.order_clause)
        self.assertIsNone(target.val.over.partition_clause)

        query = ("SELECT salary, sum(salary) "
                 "OVER (ORDER BY salary) "
                 "FROM empsalary")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 2)
        target = stmt.target_list[1]
        self.assertIsInstance(target.val, nodes.FuncCall)
        self.assertIsInstance(target.val.over, nodes.WindowDef)
        self.assertEqual(len(target.val.over.order_clause), 1)
        self.assertIsInstance(target.val.over.order_clause[0], nodes.SortBy)
        self.assertIsNone(target.val.over.partition_clause)

        query = ("SELECT salary, avg(salary) "
                 "OVER (PARTITION BY depname) "
                 "FROM empsalary")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.target_list), 2)
        target = stmt.target_list[1]
        self.assertIsInstance(target.val, nodes.FuncCall)
        self.assertIsInstance(target.val.over, nodes.WindowDef)
        self.assertIsNone(target.val.over.order_clause)
        self.assertEqual(len(target.val.over.partition_clause), 1)
        self.assertIsInstance(target.val.over.partition_clause[0],
                              nodes.ColumnRef)

    def test_select_locks(self):
        query = "SELECT m.* FROM mytable m FOR UPDATE"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.locking_clause), 1)
        self.assertIsInstance(stmt.locking_clause[0], nodes.LockingClause)
        self.assertEqual(stmt.locking_clause[0].strength, 4)

        query = "SELECT m.* FROM mytable m FOR SHARE of m nowait"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.locking_clause), 1)
        self.assertIsInstance(stmt.locking_clause[0], nodes.LockingClause)
        self.assertEqual(stmt.locking_clause[0].strength, 2)
        self.assertEqual(len(stmt.locking_clause[0].locked_rels), 1)
        self.assertIsInstance(stmt.locking_clause[0].locked_rels[0],
                              nodes.RangeVar)
        self.assertEqual(stmt.locking_clause[0].locked_rels[0].relname, 'm')
        self.assertEqual(stmt.locking_clause[0].wait_policy, 2)

    def test_select_is_null(self):
        query = "SELECT m.* FROM mytable m WHERE m.foo IS NULL"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertIsInstance(stmt.where_clause, nodes.NullTest)
        self.assertEqual(stmt.where_clause.nulltesttype, 0)

        query = "SELECT m.* FROM mytable m WHERE m.foo IS NOT NULL"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertIsInstance(stmt.where_clause, nodes.NullTest)
        self.assertEqual(stmt.where_clause.nulltesttype, 1)

    def test_select_is_true(self):
        query = "SELECT m.* FROM mytable m WHERE m.foo IS TRUE"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertIsInstance(stmt.where_clause, nodes.BooleanTest)
        self.assertEqual(stmt.where_clause.booltesttype, 0)

    def test_select_range_function(self):
        query = ("SELECT m.name AS mname, pname "
                 "FROM manufacturers m, LATERAL get_product_names(m.id) pname")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.from_clause), 2)
        second = stmt.from_clause[1]
        self.assertIsInstance(second, nodes.RangeFunction)
        self.assertTrue(second.lateral)
        self.assertEqual(len(second.functions), 1)
        self.assertEqual(len(second.functions[0]), 2)
        self.assertIsInstance(second.functions[0][0], nodes.FuncCall)

    def test_select_array(self):
        query = ("SELECT * FROM unnest(ARRAY['a','b','c','d','e','f']) "
                 "WITH ORDINALITY")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.from_clause), 1)
        outer = stmt.from_clause[0]
        self.assertIsInstance(outer, nodes.RangeFunction)
        self.assertTrue(outer.ordinality)
        self.assertEqual(len(outer.functions), 1)
        inner = outer.functions[0][0]
        self.assertIsInstance(inner, nodes.FuncCall)
        self.assertEqual(len(inner.args), 1)
        self.assertIsInstance(inner.args[0], nodes.AArrayExpr)
        self.assertEqual(len(inner.args[0].elements), 6)

    def test_select_where_in_many(self):
        query = (
            "SELECT * FROM my_table WHERE (a, b) in (('a', 'b'), ('c', 'd'))")
        stmt = parse(query).pop()
        self.assertEqual(2, len(stmt.where_clause.rexpr))
        for node in stmt.where_clause.rexpr:
            self.assertIsInstance(node, nodes.RowExpr)


class InsertQueriesTest(unittest.TestCase):

    def test_insert_no_where(self):
        query = "INSERT INTO my_table(id, name) VALUES(1, 'some')"
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.InsertStmt)
        self.assertIsNone(stmt.returning_list)

        self.assertEqual(stmt.relation.relname, 'my_table')

        self.assertEqual(len(stmt.cols), 2)
        self.assertEqual(stmt.cols[0].name, 'id')
        self.assertEqual(stmt.cols[1].name, 'name')

        self.assertIsInstance(stmt.select_stmt, nodes.SelectStmt)
        self.assertEqual(len(stmt.select_stmt.values_lists), 1)

    def test_insert_select(self):
        query = "INSERT INTO my_table(id, name) SELECT 1, 'some'"
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.InsertStmt)

        self.assertIsInstance(stmt.select_stmt, nodes.SelectStmt)
        targets = stmt.select_stmt.target_list
        self.assertEqual(len(targets), 2)
        self.assertIsInstance(targets[0], nodes.ResTarget)
        self.assertEqual(int(targets[0].val.val), 1)
        self.assertIsInstance(targets[1], nodes.ResTarget)
        self.assertEqual(str(targets[1].val.val), 'some')

    def test_insert_returning(self):
        query = "INSERT INTO my_table(id) VALUES (5) RETURNING id, \"date\""
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.InsertStmt)
        self.assertEqual(len(stmt.returning_list), 2)
        self.assertIsInstance(stmt.returning_list[0], nodes.ResTarget)
        self.assertEqual(str(stmt.returning_list[0].val.fields[0]), 'id')
        self.assertIsInstance(stmt.returning_list[1], nodes.ResTarget)
        self.assertEqual(str(stmt.returning_list[1].val.fields[0]), 'date')


class UpdateQueriesTest(unittest.TestCase):

    def test_update_to_default(self):
        query = "UPDATE my_table SET the_value = DEFAULT"
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.UpdateStmt)
        self.assertEqual(len(stmt.target_list), 1)
        self.assertIsInstance(stmt.target_list[0], nodes.ResTarget)
        self.assertIsInstance(stmt.target_list[0].val, nodes.SetToDefault)

    def test_update_array(self):
        query = ("UPDATE tictactoe "
                 "SET board[1:3][1:3] = "
                 "'{{" "," "," "},{" "," "," "},{" "," "," "}}' "
                 "WHERE game = 1")
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.UpdateStmt)
        self.assertEqual(len(stmt.target_list), 1)
        self.assertIsInstance(stmt.target_list[0], nodes.ResTarget)
        indirection = stmt.target_list[0].indirection
        self.assertEqual(len(indirection), 2)
        self.assertIsInstance(indirection[0], nodes.AIndices)
        self.assertIsInstance(indirection[1], nodes.AIndices)
        self.assertIsInstance(indirection[0].lidx, nodes.AConst)
        self.assertIsInstance(indirection[0].uidx, nodes.AConst)

    def test_update_multi_assign(self):
        query = ("UPDATE accounts "
                 "SET (contact_first_name, contact_last_name) "
                 "= (SELECT first_name, last_name FROM salesmen "
                 "WHERE salesmen.id = accounts.sales_id)")
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.UpdateStmt)
        self.assertEqual(len(stmt.target_list), 2)
        self.assertIsInstance(stmt.target_list[0], nodes.ResTarget)
        first = stmt.target_list[0]
        self.assertIsInstance(first, nodes.ResTarget)
        self.assertEqual(first.name, 'contact_first_name')
        self.assertIsInstance(first.val, nodes.MultiAssignRef)
        self.assertEqual(first.val.ncolumns, 2)
        self.assertEqual(first.val.colno, 1)
        self.assertIsInstance(first.val.source, nodes.SubLink)
        self.assertIsInstance(first.val.source.subselect, nodes.SelectStmt)


class MultipleQueriesTest(unittest.TestCase):

    def test_has_insert_and_select_statement(self):
        query = ("INSERT INTO my_table(id) VALUES(1); "
                 "SELECT * FROM my_table")
        stmts = parse(query)
        stmt_types = [type(stmt) for stmt in stmts]
        self.assertListEqual([nodes.InsertStmt, nodes.SelectStmt], stmt_types)

    def test_has_update_and_delete_statement(self):
        query = ("UPDATE my_table SET id = 5; "
                 "DELETE FROM my_table")
        stmts = parse(query)
        stmt_types = [type(stmt) for stmt in stmts]
        self.assertListEqual([nodes.UpdateStmt, nodes.DeleteStmt], stmt_types)


class WrongQueriesTest(unittest.TestCase):

    def test_syntax_error_select_statement(self):
        query = "SELECT * FRO my_table"
        try:
            parse(query)
            self.fail('Syntax error not generating an PSqlParseError')
        except PSqlParseError as e:
            self.assertEqual(e.cursorpos, 10)
            self.assertEqual(e.message, 'syntax error at or near "FRO"')

    def test_incomplete_insert_statement(self):
        query = "INSERT INTO my_table"
        try:
            parse(query)
            self.fail('Syntax error not generating an PSqlParseError')
        except PSqlParseError as e:
            self.assertEqual(e.cursorpos, 21)
            self.assertEqual(e.message, 'syntax error at end of input')

    def test_case_no_value(self):
        query = ("SELECT a, CASE WHEN a=1 THEN 'one' WHEN a=2 THEN "
                 " ELSE 'other' END FROM test")
        try:
            parse(query)
            self.fail('Syntax error not generating an PSqlParseError')
        except PSqlParseError as e:
            self.assertEqual(e.cursorpos, 51)
            self.assertEqual(e.message, 'syntax error at or near "ELSE"')


class TablesTest(unittest.TestCase):

    def test_simple_select(self):
        query = "SELECT * FROM table_one, table_two"
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'table_one', 'table_two'})

    def test_simple_select_using_schema_names(self):
        query = "SELECT * FROM table_one, public.table_one"
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'table_one', 'public.table_one'})

    def test_select_with(self):
        query = ("WITH fake_table AS (SELECT * FROM inner_table) "
                 "SELECT * FROM fake_table")
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'inner_table', 'fake_table'})

    def test_update_subquery(self):
        query = ("UPDATE dataset SET a = 5 WHERE "
                 "id IN (SELECT * from table_one) OR"
                 " age IN (select * from table_two)")
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(),
                         {'table_one', 'table_two', 'dataset'})

    def test_update_from(self):
        query = "UPDATE dataset SET a = 5 FROM extra WHERE b = c"
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'dataset', 'extra'})

    def test_join(self):
        query = ("SELECT * FROM table_one JOIN table_two USING (common_1)"
                 " JOIN table_three USING (common_2)")
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(),
                         {'table_one', 'table_two', 'table_three'})

    def test_insert_select(self):
        query = "INSERT INTO table_one(id, name) SELECT * from table_two"
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'table_one', 'table_two'})

    def test_insert_with(self):
        query = ("WITH fake as (SELECT * FROM inner_table) "
                 "INSERT INTO dataset SELECT * FROM fake")
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'inner_table', 'fake', 'dataset'})

    def test_delete(self):
        query = ("DELETE FROM dataset USING table_one "
                 "WHERE x = y OR x IN (SELECT * from table_two)")
        stmt = parse(query).pop()
        self.assertEqual(stmt.tables(), {'dataset', 'table_one',
                                         'table_two'})

    def test_select_union(self):
        query = "select * FROM table_one UNION select * FROM table_two"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertEqual(stmt.tables(), {'table_one', 'table_two'})

    def test_where_in_expr(self):
        query = "SELECT * FROM my_table WHERE (a, b) in ('a', 'b')"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(stmt.tables(), {'my_table'})

    def test_where_in_expr_many(self):
        query = (
            "SELECT * FROM my_table WHERE (a, b) in (('a', 'b'), ('c', 'd'))")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(stmt.tables(), {'my_table'})

    def test_select_target_list(self):
        query = "SELECT (SELECT * FROM table_one)"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(stmt.tables(), {'table_one'})

    def test_func_call(self):
        query = "SELECT my_func((select * from table_one))"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)
        self.assertEqual(stmt.tables(), {'table_one'})
