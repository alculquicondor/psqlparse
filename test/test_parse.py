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
        self.assertDictEqual({'str': '~~'},
                             stmt.where_clause.obj['A_Expr']['name'][0]['String'])

    def test_select_join(self):
        query = "SELECT * FROM table_one JOIN table_two USING (common)"
        stmt = parse(query).pop()

    @unittest.skip
    def test_select_with(self):
        self.fail()

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

    @unittest.expectedFailure
    def test_syntax_error_select_statement(self):
        query = "SELECT * FRO my_table"
        try:
            parse(query)
        except PSqlParseError as e:
            self.fail()
