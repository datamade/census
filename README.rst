======
census
======

A simple wrapper for the United States Census Bureau's API.

Provides access to ACS, SF1, and SF3 data sets.


Usage
=====

First, get yourself a `Census API key <http://www.census.gov/developers/>`_.

::

    from census import Census
    from us import states

    c = Census("MY_API_KEY")
    c.acs.get(('NAME', 'B25034_010E'), {'for': 'state:%s' % states.MD.fips})

The call above will return the name of the geographic area and the number of
homes that were built before 1939 for the state of Maryland. Helper methods have
been created to simplify common geometry calls::

    c.acs.state(('NAME', 'B25034_010E'), states.MD.fips)

Full details on geometries and the states module can be found below.

The get method is the core data access method on both the ACS and SF1 data sets.
The first parameter is either a single string column or a tuple of columns. The
second parameter is a geoemtry dict with a `for` key and on option `in` key. The
`for` argument accepts a `"*"` wildcard character or `Census.ALL`. The wildcard
is not valid for the `in` parameter.

The default year is 2011. To access 2010 data, pass a year parameter to the
API call::

    c.acs.state(('NAME', 'B25034_010E'), states.MD.fips, year=2010)

The default year may also be set client-wide::

    c = Census("MY_API_KEY", year=2010)


Datasets
========

* ACS5: ACS 5 Year Estimates (2011, 2010)
* ACS1DP: ACS 1 Year Estimates, Data Profiles (2012)
* SF1: Census Summary File 1 (2010, 2000, 1990)
* SF3: Census Summary File 3 (2000, 1990)


Geographies
===========

The API supports a wide range of geographic regions. The specification of these
can be quite complicated so a number of convenience methods are provided. Refer to the `Census API documentation <http://www.census.gov/developers/data/>`_
for more geographies beyond the convenience methods.

*Not all geographies are supported in all years. Calling a convenience method
with a year that is not supported will raise census.UnsupportedYearException.*

`Geographic relationship files <http://www.census.gov/geo/maps-data/data/relationship.html>`_ are provided on the Census developer site as a tool to help users compare the geographies from the 1990, 2000 and 2010 Censuses. From these files, data users may determine how geographies from one Census relate to those from the prior Census.

ACS5 Geographies
--------------

* state(fields, state_fips)
* state_county(fields, state_fips, county_fips)
* state_county_subdivision(fields, state_fips, county_fips, subdiv_fips)
* state_county_tract(fields, state_fips, county_fips, tract)
* state_place(fields, state_fips, place)
* state_district(fields, state_fips, district)
* us(fields)
* zipcode(fields, zip5)

ACS1 Geographies
--------------

* state(fields, state_fips)
* state_district(fields, state_fips, district)
* us(fields)

SF1 Geographies
--------------

* state(fields, state_fips)
* state_county(fields, state_fips, county_fips)
* state_county_subdivision(fields, state_fips, county_fips, subdiv_fips)
* state_county_tract(fields, state_fips, county_fips, tract)
* state_place(fields, state_fips, place)
* state_district(fields, state_fips, district)
* state_msa(fields, state_fips, msa)
* state_csa(fields, state_fips, csa)
* state_district_place(fields, state_fips, district, place)
* state_zipcode(fields, state_fips, zip5)

SF3 Geometries
--------------

* state(fields, state_fips)
* state_county(fields, state_fips, county_fips)
* state_county_tract(fields, state_fips, county_fips, tract)
* state_place(fields, state_fips, place)


States
======

This package previously had a `census.states` module, but now uses the
*us* package. ::

    >>> from us import states
    >>> print states.MD.fips
    u'24'

Convert FIPS to state abbreviation using `lookup()`: ::

    >>> print states.lookup('24').abbr
    u'MD'


BYOS - Bring Your Own Session
=============================

If you'd prefer to use a custom configured requests.Session, you can pass it
to the Census constructor::

    s = requests.session()
    s.headers.update({'User-Agent': 'census-demo/0.0'})

    c = Census("MY_API_KEY", session=s)

You can also replace the session used by a specific data set::

    c.sf1.session = s


Examples
========

The geographic name for all census tracts for county 170 in Alaska::

    c.sf1.get('NAME', geo={'for': 'tract:*', 'in': 'state:%s county:170' % states.AK.fips})

The same call using the `state_county_tract` convenience method::

    c.sf1.state_county_tract('NAME', states.AK.fips, '170', Census.ALL)

Total number of males age 5 - 9 for all states::

    c.acs.get('B01001_004E', {'for': 'state:*'})

The same call using the state convenience method::

    c.acs.state('B01001_004E', Census.ALL)
