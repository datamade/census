======
census
======

A simple wrapper for the United States Census Bureau's API.

Provides access to both the ACS and SF1 data sets.


Requirements
============

* python 2.6 or 2.7
* requests


Usage
=====

First, get yourself a `Census API key <http://www.census.gov/developers/>`_.

::

    from census import Census

    c = Census("MY_API_KEY")

Full geometry specifications are available for `ACS <http://thedataweb.rm.census.gov/data/acs5geo.html>`_ and `SF1 <http://thedataweb.rm.census.gov/data/sf1geo.html>`_

ACS Geometries
--------------

* state(fields, state_fips)
* state_county(fields, state_fips, county_fips)
* state_county_subdivision(fields, state_fips, county_fips, subdiv_fips)
* state_county_tract(fields, state_fips, county_fips, tract)
* state_place(fields, state_fips, place)
* state_district(fields, state_fips, district)
* us(fields)


SF1 Geometries
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
* state_zip(fields, state_fips, zip)






http://www.census.gov/developers/data/sf1.xml
http://www.census.gov/developers/data/2010acs5_variables.xml

States
======

The states module makes it easy to convert between state abbreviations and FIPS
codes. Access attributes by state abbreviation to get the corresponding FIPS
code::

    >>> from census import states
    >>> print states.MD
    24

Convert FIPS to state abbreviation using the FIPS dict::

    >>> print states.FIPS['24']
    MD


Examples
========

