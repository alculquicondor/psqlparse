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


class InsertQueriesTest(unittest.TestCase):

    def test_insert(self):
        query = "INSERT INTO my_table(id) VALUES(1)"
        stmt = parse(query).pop()

        self.assertIsInstance(stmt, nodes.InsertStmt)
        self.assertIsNone(stmt.from_clause)
        self.assertIsNone(stmt.where_clause)


class MultipleQueriesTest(unittest.TestCase):

    def test_has_insert_and_select_statement(self):
        query = "INSERT INTO my_table(id) VALUES(1); SELECT * FROM my_table"
        insert_and_stmt = parse(query)
        stmt_types = [type(stmt) for stmt in insert_and_stmt]
        self.assertListEqual([nodes.InsertStmt, nodes.SelectStmt], stmt_types)


class WrongQueriesTest(unittest.TestCase):

    def test_syntax_error_select_statement(self):
        query = "SELECT * FRO my_table"
        try:
            parse(query)
            self.fail('Syntax error not generating an PSqlParseError')
        except PSqlParseError as e:
            self.assertEqual(e.cursorpos, 10)
            self.assertEqual(e.message, 'syntax error at or near "FRO"')

