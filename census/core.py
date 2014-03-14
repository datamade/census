from functools import wraps
from xml.etree.ElementTree import XML
import json
import requests

__version__ = "0.6"

ALL = '*'
ENDPOINT_URL = 'http://api.census.gov/data/%s/%s'
DEFINITIONS = {
    'acs5': {
        '2011': 'http://www.census.gov/developers/data/acs_5yr_2011_var.xml',
        '2010': 'http://www.census.gov/developers/data/acs_5yr_2010_var.xml',
    },
    'acs1/profile': {
        '2012': 'http://www.census.gov/developers/data/acs_1yr_profile_2012.xml',
    },
    'sf1': {
        '2010': 'http://www.census.gov/developers/data/sf1.xml',
        '2000': 'http://www.census.gov/developers/data/2000_sf1.xml',
        '1990': 'http://www.census.gov/developers/data/1990_sf1.xml',
    },
    'sf3': {
        '2000': 'http://www.census.gov/developers/data/2000_sf3.xml',
        '1990': 'http://www.census.gov/developers/data/1990_sf3.xml',
    },
}

class APIKeyError(Exception):
    '''Invalid API Key'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def list_or_str(v):
    """ Convert a single value into a list.
    """
    if isinstance(v, (list, tuple)):
        return v
    return [v]


def supported_years(*years):
    def inner(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            year = kwargs.get('year', self.default_year)
            if int(year) not in years:
                raise UnsupportedYearException('geography is not available in %s' % year)
            return func(self, *args, **kwargs)
        return wrapper
    return inner


class CensusException(Exception):
    pass


class UnsupportedYearException(CensusException):
    pass


class Client(object):

    def __init__(self, key, year=None, session=None):
        self._key = key
        self.session = session or requests.session()
        if year:
            self.default_year = year

    @property
    def years(self):
        return [int(y) for y in DEFINITIONS[self.dataset].keys()]

    def fields(self, year, flat=False):

        data = {}

        fields_url = DEFINITIONS[self.dataset].get(str(year))

        if not fields_url:
            raise CensusException('%s is not available for %s' % (self.dataset, year))

        resp = requests.get(fields_url)
        doc = XML(resp.text)

        if flat:

            for elem in doc.iter('variable'):
                data[elem.attrib['name']] = "%s: %s" % (elem.attrib['concept'], elem.text)

        else:

            for concept_elem in doc.iter('concept'):

                concept = concept_elem.attrib['name']
                variables = {}

                for variable_elem in concept_elem.iter('variable'):
                    variables[variable_elem.attrib['name']] = variable_elem.text

                data[concept] = variables

        return data

    def get(self, fields, geo, year=None):

        if len(fields) > 50:
            raise CensusException("only 50 columns per call are allowed")

        if year is None:
            year = self.default_year

        fields = list_or_str(fields)

        url = ENDPOINT_URL % (year, self.dataset)

        params = {
            'get': ",".join(fields),
            'for': geo['for'],
            'key': self._key,
        }

        if 'in' in geo:
            params['in'] = geo['in']

        headers = {
            'User-Agent': 'python-census/%s github.com/sunlightlabs/census' % __version__
        }
        resp = self.session.get(url, params=params, headers=headers)

        if resp.status_code == 200:
            try:
                data = json.loads(resp.text)
            except ValueError as ex:
                if '<title>Invalid Key</title>' in resp.text:
                    raise APIKeyError(' '.join(resp.text.splitlines()))
                else:
                    raise ex

            headers = data[0]
            return [dict(zip(headers, d)) for d in data[1:]]

        elif resp.status_code == 204:
            return []

        else:
            raise CensusException(resp.text)


class ACS5Client(Client):

    default_year = 2011
    dataset = 'acs5'

    @supported_years(2011, 2010)
    def us(self, fields, **kwargs):
        return self.get(fields, geo={'for': 'us:1'}, **kwargs)

    @supported_years(2011, 2010)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2011, 2010)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:%s' % county_fips,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2011, 2010)
    def state_county_subdivision(self, fields, state_fips, county_fips, subdiv_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county subdivision:%s' % subdiv_fips,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    @supported_years(2011, 2010)
    def state_county_tract(self, fields, state_fips, county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:%s' % tract,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    @supported_years(2011, 2010)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:%s' % place,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2011, 2010)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:%s' % district,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2011)
    def zipcode(self, fields, zcta, **kwargs):
        return self.get(fields, geo={
            'for': 'zip code tabulation area:%s' % zcta,
        }, **kwargs)

class ACS1DpClient(Client):

    default_year = 2012
    dataset = 'acs1/profile'

    @supported_years(2012)
    def us(self, fields, **kwargs):
        return self.get(fields, geo={'for': 'us:1'}, **kwargs)

    @supported_years(2012)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2012)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:%s' % district,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

class SF1Client(Client):

    default_year = 2010
    dataset = 'sf1'

    @supported_years(2010, 2000, 1990)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:%s' % county_fips,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010)
    def state_county_subdivision(self, fields, state_fips, county_fips, subdiv_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county subdivision:%s' % subdiv_fips,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_county_tract(self, fields, state_fips, county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:%s' % tract,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:%s' % place,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:%s' % district,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010)
    def state_msa(self, fields, state_fips, msa, **kwargs):
        return self.get(fields, geo={
            'for': 'metropolitan statistical area/micropolitan statistical area:%s' % msa,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010)
    def state_csa(self, fields, state_fips, csa, **kwargs):
        return self.get(fields, geo={
            'for': 'combined statistical area:%s' % csa,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2010)
    def state_district_place(self, fields, state_fips, district, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:' % place,
            'in': 'state:%s congressional district:%s' % (state_fips, district),
        }, **kwargs)

    @supported_years(2010)
    def state_zipcode(self, fields, state_fips, zcta, **kwargs):
        return self.get(fields, geo={
            'for': 'zip code tabulation area:%s' % zcta,
            'in': 'state:%s' % state_fips,
        }, **kwargs)


class SF3Client(Client):

    default_year = 2000
    dataset = 'sf3'

    @supported_years(2000, 1990)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:%s' % county_fips,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_county_tract(self, fields, state_fips, county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:%s' % tract,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:%s' % place,
            'in': 'state:%s' % state_fips,
        }, **kwargs)


class Census(object):

    ALL = ALL

    def __init__(self, key, year=None, session=None):

        if not session:
            session = requests.session()

        self.acs = ACS5Client(key, year, session)
        self.acs5 = ACS5Client(key, year, session)
        self.acs1dp = ACS1DpClient(key, year, session)
        self.sf1 = SF1Client(key, year, session)
        self.sf3 = SF3Client(key, year, session)
