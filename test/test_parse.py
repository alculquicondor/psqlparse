import unittest

import psqlparse


class TestParse(unittest.TestCase):

    def test_is_select_statement(self):
        query = "SELECT * FROM my_table"
        select_stmt = psqlparse.parse(query).pop()
        self.assertEqual(select_stmt.type, "SelectStmt")

    def test_has_insert_and_select_statement(self):
        query = "INSERT INTO my_table(id) VALUES(1); SELECT * FROM my_table"
        insert_and_select_stmt = psqlparse.parse(query)
        stmt_types = [stmt.type for stmt in insert_and_select_stmt]
        self.assertListEqual(stmt_types, ['InsertStmt', 'SelectStmt'])

    def test_syntax_error_select_statement(self):
        query = "SELECT * FRO my_table"
        try:
            psqlparse.parse(query)
        except Exception as e:
            exception = e
        self.assertIsInstance(exception, psqlparse.exceptions.PSqlParseError)
