import unittest

from psqlparse import normalize
from psqlparse.exceptions import PSqlParseError
from psqlparse import nodes


class NormalizeTest(unittest.TestCase):
    def test_simple(self):
        query = "SELECT * FROM mytable WHERE col1 = 1"
        self.assertEqual(normalize(query), "SELECT * FROM mytable WHERE col1 = $1")
