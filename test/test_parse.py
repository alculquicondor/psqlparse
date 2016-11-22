import unittest

from psqlparse import parse
from psqlparse.exceptions import PSqlParseError
from psqlparse.nodes import WhereClause


class TestParse(unittest.TestCase):

    def test_select_all_no_where(self):
        query = "SELECT * FROM my_table"
        stmt = parse(query).pop()
        self.assertEqual(stmt.type, "SelectStmt")
        self.assertIsNone(stmt.where_clause)
        target = stmt.target_list.targets.pop()
        self.assertDictEqual({'A_Star': {}},
                             target['val']['ColumnRef']['fields'][0])

    def test_select_one_column_where(self):
        query = "SELECT col1 FROM my_table WHERE my_attribute LIKE condition"
        stmt = parse(query).pop()
        self.assertEqual(stmt.type, "SelectStmt")
        self.assertIsInstance(stmt.where_clause, WhereClause)
        target = stmt.target_list.targets.pop()
        self.assertDictEqual({'str': 'col1'},
                             target['val']['ColumnRef']['fields'][0]['String'])
        self.assertDictEqual({'str': '~~'}, stmt.where_clause
                             .obj['A_Expr']['name'][0]['String'])

    def test_select_join(self):
        query = "SELECT * FROM table_one JOIN table_two USING (common)"
        stmt = parse(query).pop()
        self.assertEqual(stmt.type, 'SelectStmt')

    def test_select_with(self):
        query = ("WITH fake_table AS (SELECT SUM(countable) AS total "
                 "FROM inner_table GROUP BY groupable) "
                 "SELECT * FROM fake_table")
        stmt = parse(query).pop()
        self.assertEqual('SelectStmt',
                         stmt.with_clause.queries['fake_table'].type)
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
