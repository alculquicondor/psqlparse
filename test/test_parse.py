import unittest

from psqlparse import parse
from psqlparse.exceptions import PSqlParseError
from psqlparse import nodes


class TestParse(unittest.TestCase):

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
                 "WHERE my_attribute LIKE 'condition'")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

        self.assertEqual(len(stmt.target_list), 1)
        target = stmt.target_list[0]
        self.assertIsInstance(target, nodes.ResTarget)
        self.assertEqual(target.val.fields[0].str, 'col1')

        self.assertIsInstance(stmt.where_clause, nodes.AExpr)
        expr = stmt.where_clause
        self.assertEqual(expr.lexpr.fields[0].str, 'my_attribute')
        self.assertEqual(expr.rexpr.val.str, 'condition')

    def test_select_join(self):
        query = "SELECT * FROM table_one JOIN table_two USING (common)"
        stmt = parse(query).pop()
        self.assertIsInstance(stmt, nodes.SelectStmt)

    def test_select_with(self):
        query = ("WITH fake_table AS (SELECT SUM(countable) AS total "
                 "FROM inner_table GROUP BY groupable) "
                 "SELECT * FROM fake_table")
        stmt = parse(query).pop()
        self.assertIsInstance(stmt.with_clause, nodes.WithClause)
        self.assertEqual(len(stmt.with_clause.ctes), 1)
        with_query = stmt.with_clause.ctes[0]
        # self.assertEqual('SelectStmt',
        #                  stmt.with_clause.queries['fake_table'].type)
        self.assertIsNone(stmt.with_clause.recursive)

    def test_select_subquery(self):
        query = "select * FROM (select something from dataset) as other"
        stmt = parse(query).pop()
        self.assertEqual(stmt.type, 'SelectStmt')
        self.assertEqual(len(stmt.from_clause.items), 1)
        self.assertEqual(len(stmt.target_list.targets), 1)

    def test_insert(self):
        query = "INSERT INTO my_table(id) VALUES(1)"
        stmt = parse(query).pop()
        self.assertEqual('InsertStmt', stmt.type)
        self.assertIsNone(stmt.from_clause)
        self.assertIsNone(stmt.where_clause)

    def test_has_insert_and_select_statement(self):
        query = "INSERT INTO my_table(id) VALUES(1); SELECT * FROM my_table"
        insert_and_stmt = parse(query)
        stmt_types = [stmt.type for stmt in insert_and_stmt]
        self.assertListEqual(['InsertStmt', 'SelectStmt'], stmt_types)

    def test_syntax_error_select_statement(self):
        query = "SELECT * FRO my_table"
        try:
            parse(query)
            self.fail('Syntax error not generating an PSqlParseError')
        except PSqlParseError as e:
            self.assertEqual(e.cursorpos, 10)
            self.assertEqual(e.message, 'syntax error at or near "FRO"')
