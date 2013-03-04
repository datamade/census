import os
import unittest

from core import Census, UnsupportedYearException

KEY = os.environ.get('CENSUS_KEY', '')


class TestUnsupportedYears(unittest.TestCase):

    def setUp(self):
        self.client = Census(KEY, year=2008)

    def test_acs(self):
        self.assertRaises(UnsupportedYearException,
                          self.client.acs.state, ('NAME', '06'))

    def test_sf1(self):
        self.assertRaises(UnsupportedYearException,
                          self.client.sf1.state, ('NAME', '06'))

    def test_sf3(self):
        self.assertRaises(UnsupportedYearException,
                          self.client.sf3.state, ('NAME', '06'))


if __name__ == '__main__':
    unittest.main()
