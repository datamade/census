import os
import time
import unittest
from contextlib import closing

import requests

from census import (
    Census, UnsupportedYearException, __version__)
from census.core import DEFINITIONS

KEY = os.environ.get('CENSUS_KEY', '')

CLIENTS = (
    ('acs5', (
        'us', 'state', 'state_county', 'state_county_subdivision',
        'state_county_tract', 'state_county_blockgroup',
        'state_place', 'state_district', 'zipcode',
    )),
    ('acs1dp', (
        'us', 'state', 'state_district',
    )),
    ('sf1', (
        'state', 'state_county', 'state_county_subdivision',
        'state_county_tract', 'state_county_blockgroup',
        'state_place', 'state_district', 'state_msa', 'state_csa',
        'state_district_place', 'state_zipcode',
    )),
    ('sf3', (
        'state', 'state_county', 'state_county_tract',
        'state_county_blockgroup', 'state_place',
    )),
)

TEST_DATA = {
    'state_fips': '24',
    'county_fips': '31',
    'subdiv_fips': '90796',
    'tract': '700704',
    'blockgroup': '1',
    'place': '31175',
    'district': '06',
    'zcta': '20877',
    'msa': '47900',
    'csa': '548',
}


class CensusTestCase(unittest.TestCase):

    def setUp(self):
        self._client = Census(KEY)

    def client(self, name):
        return getattr(self._client, name)

    def tearDown(self):
        self._client.session.close()


class TestDataDefinitions(CensusTestCase):

    def test_valid_json(self):

        with closing(requests.Session()) as http:

            http.headers = {
                'User-Agent': ('python-census/{}/tests '.format(__version__) +
                               'github.com/sunlightlabs/census')
            }

            for name, datasets in DEFINITIONS.items():
                for year, url in datasets.items():
                    resp = http.head(url)
                    self.assertEqual(resp.status_code, 200)


class TestDefaultYears(CensusTestCase):

    def test_default_year_is_supported(self):

        for client_name, method_names in CLIENTS:
            client = self.client(client_name)
            for method_name in method_names:
                method = getattr(client, method_name)
                self.assertIn(client.default_year, method.supported_years)


# class TestSupportedYears(CensusTestCase):
#
#     def test_acs5(self):
#         pass


class TestUnsupportedYears(CensusTestCase):

    def setUp(self):
        self._client = Census(KEY, year=2008)

    def test_acs5(self):
        client = self.client('acs5')
        self.assertRaises(UnsupportedYearException,
                          client.state, ('NAME', '06'))

    def test_acs1dp(self):
        client = self.client('acs1dp')
        self.assertRaises(UnsupportedYearException,
                          client.state, ('NAME', '06'))

    def test_sf1(self):
        client = self.client('sf1')
        self.assertRaises(UnsupportedYearException,
                          client.state, ('NAME', '06'))

    def test_sf3(self):
        client = self.client('sf3')
        self.assertRaises(UnsupportedYearException,
                          client.state, ('NAME', '06'))


class TestEndpoints(CensusTestCase):

    def check_endpoints(self, client_name, tests, **kwargs):

        if kwargs:
            tests = ((k, kwargs.get(k, v)) for k, v in tests)

        client = self.client(client_name)
        fields = ('NAME',)

        for method_name, expected in tests:

            msg = '{}.{}'.format(client_name, method_name)

            method = getattr(client, method_name)
            data = method(fields, **TEST_DATA)
            self.assertTrue(data, msg)
            self.assertEqual(data[0]['NAME'], expected, msg)
            time.sleep(0.2)

    def test_acs5(self):

        tests = (
            ('us', 'United States'),
            ('state', 'Maryland'),
            ('state_county', 'Montgomery County, Maryland'),
            ('state_county_subdivision',
                'District 9, Montgomery County, Maryland'),
            ('state_county_tract',
                'Census Tract 7007.04, Montgomery County, Maryland'),
            ('state_county_blockgroup',
                ('Block Group 1, Census Tract 7007.04, '
                    'Montgomery County, Maryland')),
            ('state_place', 'Gaithersburg city, Maryland'),
            ('state_district',
                'Congressional District 6 (114th Congress), Maryland'),
            ('zipcode', 'ZCTA5 20877'),
        )

        self.check_endpoints('acs5', tests)

    def test_acs1dp(self):

        tests = (
            ('us', 'United States'),
            ('state', 'Maryland'),
            ('state_district',
                'Congressional District 6 (113th Congress), Maryland'),
        )

        self.check_endpoints('acs1dp', tests)

    def test_sf1(self):

        tests = (
            ('state', 'Maryland'),
            ('state_county', 'Montgomery County'),
            ('state_county_subdivision', 'District 9'),
            ('state_county_tract',
                'Census Tract 7007.04'),
            ('state_county_blockgroup', 'Block Group 1'),
            ('state_place', 'Gaithersburg city'),
            ('state_district', 'Congressional District 6'),
            ('state_msa',
                ('Washington-Arlington-Alexandria, '
                    'DC-VA-MD-WV Metro Area (part)')),
            ('state_csa',
                ('Washington-Baltimore-Northern Virginia, '
                    'DC-MD-VA-WV CSA (part)')),
            # ('state_district_place', 'District 9'),
            ('state_zipcode', 'ZCTA5 20877'),
        )

        self.check_endpoints('sf1', tests)

    def test_sf3(self):

        tests = (
            ('state', 'Maryland'),
            ('state_county', 'Montgomery County'),
            ('state_county_tract',
                'Census Tract 7007.04'),
            ('state_county_blockgroup', 'Block Group 1'),
            ('state_place', 'Gaithersburg city'),
        )

        self.check_endpoints('sf3', tests)

    def test_more_than_50(self):
        fields = ['B01001_003E', 'B01001_004E', 'B01001_005E',
                  'B01001_006E', 'B01001_007E', 'B01001_008E',
                  'B01001_009E', 'B01001_010E', 'B01001_011E',
                  'B01001_012E', 'B01001_013E', 'B01001_014E',
                  'B01001_015E', 'B01001_016E', 'B01001_017E',
                  'B01001_018E', 'B01001_019E', 'B01001_020E',
                  'B01001_021E', 'B01001_022E', 'B01001_023E',
                  'B01001_024E', 'B01001_025E', 'B01001_027E',
                  'B01001_028E', 'B01001_029E', 'B01001_030E',
                  'B01001_031E', 'B01001_032E', 'B01001_033E',
                  'B01001_034E', 'B01001_035E', 'B01001_036E',
                  'B01001_037E', 'B01001_038E', 'B01001_039E',
                  'B01001_040E', 'B01001_041E', 'B01001_042E',
                  'B01001_043E', 'B01001_044E', 'B01001_045E',
                  'B01001_046E', 'B01001_047E', 'B01001_048E',
                  'B01001_049E', 'B19001_003E', 'B19001_004E',
                  'B19001_005E', 'B19001_006E', 'B19001_007E',
                  'B19001_008E', 'B19001_009E', 'B19001_010E',
                  'B19001_011E', 'B19001_012E', 'B19001_013E',
                  'B19001_014E', 'B19001_015E', 'B19001_016E']

        client = self.client('acs5')
        results = client.us(fields)
        assert set(results[0].keys()).issuperset(fields)

if __name__ == '__main__':
    unittest.main()
