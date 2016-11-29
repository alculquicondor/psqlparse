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
    
    def test_select_order_by_default(self):
        query = "SELECT * FROM my_table ORDER BY my_table.id"
        stmt = parse(query).pop()
        orderby = stmt.sort_clause.pop()

        self.assertIsInstance(orderby, nodes.parsenodes.SortBy)
        self.assertEqual(len(orderby.node.fields), 2)

        name_column = orderby.node.fields.pop()
        name_table = orderby.node.fields.pop()

        self.assertEqual(str(name_column), 'id')
        self.assertEqual(str(name_table), 'my_table')


    def test_select_union(self):
        query = "select * FROM table_one UNION select * FROM table_two"
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

