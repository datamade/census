import json
import warnings
from functools import wraps

__version__ = "0.8.1"

ALL = '*'
ENDPOINT_URL = 'http://api.census.gov/data/%s/%s'
DEFINITIONS = {
    'acs5': {
        '2014': 'http://api.census.gov/data/2014/acs5/variables.json',
        '2013': 'http://api.census.gov/data/2013/acs5/variables.json',
        '2012': 'http://api.census.gov/data/2012/acs5/variables.json',
        '2011': 'http://api.census.gov/data/2011/acs5/variables.json',
        '2010': 'http://api.census.gov/data/2010/acs5/variables.json',
    },
    'acs1/profile': {
        '2012': 'http://api.census.gov/data/2012/acs1/variables.json',
    },
    'sf1': {
        '2010': 'http://api.census.gov/data/2010/sf1/variables.json',
        '2000': 'http://api.census.gov/data/2000/sf1/variables.json',
        '1990': 'http://api.census.gov/data/1990/sf1/variables.json',
    },
    'sf3': {
        '2000': 'http://api.census.gov/data/2000/sf3/variables.json',
        '1990': 'http://api.census.gov/data/1990/sf3/variables.json',
    },
}


def new_session(*args, **kwargs):
    import requests
    return requests.session(*args, **kwargs)


class APIKeyError(Exception):
    """ Invalid API key
    """

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
                raise UnsupportedYearException(
                    'geography is not available in {}'.format(year))
            return func(self, *args, **kwargs)
        wrapper.supported_years = years
        return wrapper
    return inner


class CensusException(Exception):
    pass


class UnsupportedYearException(CensusException):
    pass


class Client(object):

    def __init__(self, key, year=None, session=None):
        self._key = key
        self.session = session or new_session()
        if year:
            self.default_year = year

    @property
    def years(self):
        return [int(y) for y in DEFINITIONS[self.dataset].keys()]

    def fields(self, year=None, flat=False):
        if year is None:
            year = self.default_year

        data = {}

        fields_url = DEFINITIONS[self.dataset].get(str(year))

        if not fields_url:
            raise CensusException(
                '{} is not available for {}'.format(self.dataset, year))

        resp = self.session.get(fields_url)
        obj = json.loads(resp.text)

        if flat:

            for key, elem in obj['variables'].items():
                if key in ['for', 'in']:
                    continue
                data[key] = "{}: {}".format(elem['concept'], elem['label'])

        else:

            data = obj['variables']
            if 'for' in data:
                data.pop("for", None)
            if 'in' in data:
                data.pop("in", None)

        return data

    def get(self, fields, geo, year=None, **kwargs):

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
            'User-Agent': ('python-census/{} '.format(__version__) +
                           'github.com/sunlightlabs/census')
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

    default_year = 2014
    dataset = 'acs5'

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def us(self, fields, **kwargs):
        return self.get(fields, geo={'for': 'us:1'}, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:{}'.format(county_fips),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_county_subdivision(self, fields, state_fips,
                                 county_fips, subdiv_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county subdivision:{}'.format(subdiv_fips),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_county_tract(self, fields, state_fips,
                           county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:{}'.format(tract),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_county_blockgroup(self, fields, state_fips, county_fips,
                                blockgroup, tract=None, **kwargs):
        geo = {
            'for': 'block group:{}'.format(blockgroup),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }
        if tract:
            geo['in'] += ' tract:{}'.format(tract)
        return self.get(fields, geo=geo, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:{}'.format(place),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:{}'.format(district),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2014, 2013, 2012, 2011)
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
            'for': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2012)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:{}'.format(district),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)


class SF1Client(Client):

    default_year = 2010
    dataset = 'sf1'

    @supported_years(2010, 2000, 1990)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:{}'.format(county_fips),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010, 2000)
    def state_county_subdivision(self, fields, state_fips,
                                 county_fips, subdiv_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county subdivision:{}'.format(subdiv_fips),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_county_tract(self, fields, state_fips,
                           county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:{}'.format(tract),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_county_blockgroup(self, fields, state_fips, county_fips,
                                blockgroup, tract=None, **kwargs):
        geo = {
            'for': 'block group:{}'.format(blockgroup),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }
        if tract:
            geo['in'] += ' tract:{}'.format(tract)
        return self.get(fields, geo=geo, **kwargs)

    @supported_years(2010, 2000, 1990)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:{}'.format(place),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010)
    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:{}'.format(district),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010)
    def state_msa(self, fields, state_fips, msa, **kwargs):
        return self.get(fields, geo={
            'for': ('metropolitan statistical area/' +
                    'micropolitan statistical area:{}'.format(msa)),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010)
    def state_csa(self, fields, state_fips, csa, **kwargs):
        return self.get(fields, geo={
            'for': 'combined statistical area:{}'.format(csa),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2010)
    def state_district_place(self, fields, state_fips,
                             district, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:{}'.format(place),
            'in': 'state:{} congressional district:{}'.format(
                state_fips, district),
        }, **kwargs)

    @supported_years(2010)
    def state_zipcode(self, fields, state_fips, zcta, **kwargs):
        return self.get(fields, geo={
            'for': 'zip code tabulation area:{}'.format(zcta),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)


class SF3Client(Client):

    default_year = 2000
    dataset = 'sf3'

    @supported_years(2000, 1990)
    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:{}'.format(county_fips),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_county_tract(self, fields, state_fips,
                           county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:{}'.format(tract),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }, **kwargs)

    @supported_years(2000, 1990)
    def state_county_blockgroup(self, fields, state_fips, county_fips,
                                blockgroup, tract=None, **kwargs):
        geo = {
            'for': 'block group:{}'.format(blockgroup),
            'in': 'state:{} county:{}'.format(state_fips, county_fips),
        }
        if tract:
            geo['in'] += ' tract:{}'.format(tract)
        return self.get(fields, geo=geo, **kwargs)

    @supported_years(2000, 1990)
    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:{}'.format(place),
            'in': 'state:{}'.format(state_fips),
        }, **kwargs)


class Census(object):

    ALL = ALL

    def __init__(self, key, year=None, session=None):

        if not session:
            session = new_session()

        self.session = session

        self._acs = ACS5Client(key, year, session)  # deprecated
        self.acs5 = ACS5Client(key, year, session)
        self.acs1dp = ACS1DpClient(key, year, session)
        self.sf1 = SF1Client(key, year, session)
        self.sf3 = SF3Client(key, year, session)

    @property
    def acs(self):
        warnings.warn('Use acs5 instead of acs', DeprecationWarning)
        return self._acs
