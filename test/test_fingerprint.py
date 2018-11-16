import unittest

from psqlparse import fingerprint
from psqlparse.exceptions import PSqlParseError
from psqlparse import nodes


class FingerprintTest(unittest.TestCase):
    def test_simple(self):
        query1 = "SELECT * FROM mytable WHERE col1 = 1"
        query2 = "SELECT * FROM mytable WHERE col1 = 2"
        query3 = """SELECT *
                    FROM mytable
                    WHERE col1 = 2"""
        assert fingerprint(query1) == fingerprint(query2)
        assert fingerprint(query1) == fingerprint(query3)
