import json
import requests
from xml.etree.ElementTree import XML

ALL = '*'
ENDPOINT_URL = 'http://api.census.gov/data/%s/%s'


def list_or_str(v):
    """ Convert a single value into a list.
    """
    if isinstance(v, (list, tuple)):
        return v
    return [v]


class CensusException(Exception):
    pass


class Client(object):

    def __init__(self, key):
        self._session = requests.session()
        self._key = key

    def fields(self, flat=False):

        data = {}

        resp = requests.get(self.fields_url)
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

        resp = self._session.get(url, params=params)

        if resp.status_code == 200:

            data = json.loads(resp.text)
            # return data

            headers = data[0]
            return [dict(zip(headers, d)) for d in data[1:]]

        elif resp.status_code == 204:
            return []

        else:
            raise CensusException(resp.text)

    def state(self, fields, state_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'state:%s' % state_fips,
        }, **kwargs)

    def state_county(self, fields, state_fips, county_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county:%s' % county_fips,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    def state_county_subdivision(self, fields, state_fips, county_fips, subdiv_fips, **kwargs):
        return self.get(fields, geo={
            'for': 'county subdivision:%s' % subdiv_fips,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    def state_county_tract(self, fields, state_fips, county_fips, tract, **kwargs):
        return self.get(fields, geo={
            'for': 'tract:%s' % tract,
            'in': 'state:%s county:%s' % (state_fips, county_fips),
        }, **kwargs)

    def state_place(self, fields, state_fips, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:%s' % place,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    def state_district(self, fields, state_fips, district, **kwargs):
        return self.get(fields, geo={
            'for': 'congressional district:%s' % district,
            'in': 'state:%s' % state_fips,
        }, **kwargs)


class ACSClient(Client):

    default_year = 2011
    dataset = 'acs5'
    fields_url = "http://www.census.gov/developers/data/2010acs5_variables.xml"

    def us(self, fields, **kwargs):
        return self.get(fields, geo={'for': 'us:1'}, **kwargs)


class SF1Client(Client):

    default_year = 2011
    dataset = 'sf1'
    fields_url = "http://www.census.gov/developers/data/sf1.xml"

    def state_msa(self, fields, state_fips, msa, **kwargs):
        return self.get(fields, geo={
            'for': 'metropolitan statistical area/micropolitan statistical area:%s' % msa,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    def state_csa(self, fields, state_fips, csa, **kwargs):
        return self.get(fields, geo={
            'for': 'combined statistical area:%s' % csa,
            'in': 'state:%s' % state_fips,
        }, **kwargs)

    def state_district_place(self, fields, state_fips, district, place, **kwargs):
        return self.get(fields, geo={
            'for': 'place:' % place,
            'in': 'state:%s congressional district:%s' % (state_fips, district),
        }, **kwargs)

    def state_zip(self, fields, state_fips, zip, **kwargs):
        return self.get(fields, geo={
            'for': 'zip code tabulation area:%s' % zip,
            'in': 'state:%s' % state_fips,
        }, **kwargs)


class Census(object):

    def __init__(self, key):
        self.acs = ACSClient(key)
        self.sf1 = SF1Client(key)
