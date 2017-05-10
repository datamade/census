import json
import sys
import logging

import esridump
import shapely.geometry
import shapely.geos

import .core as core
from .core import supported_years

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

GEO_URLS = {
    'tracts' : {
        1990 : 'https://gis.uspatial.umn.edu/arcgis/rest/services/nhgis/Census_Tracts_1910_2014/MapServer/8',
        2000 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/6',
        2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2011 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2012 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/8',
        2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/8',
        2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/8',
        2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/8'},
    'block groups' : {
        2000 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/8',
        2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2011 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2012 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/10',
        2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/10',
        2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/10',
        2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/10'},
    'blocks' : {
        2000 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/10',
        2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/12'},
    'incorporated places' : {
        1990 : 'https://gis.uspatial.umn.edu/arcgis/rest/services/nhgis/Places_1980_2014/MapServer/1',
        2000 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/24',
        2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2011 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2012 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/26',
        2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/26',
        2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/26',
        2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2016/MapServer/26'}
}


class AreaFilter(object):
    def __init__(self, geojson_geometry, sub_geography_url):
        self.geo = shapely.geometry.shape(geojson_geometry)

        geo_query_args = {'geometry': ','.join(str(x) for x in self.geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR' : '4326',
                          'geometryPrecision' : 9,
                          'orderByFields': 'OID'}
        self.area_dumper = esridump.EsriDumper(sub_geography_url,
                                               extra_query_args = geo_query_args)

    def __iter__(self):
        for area in self.area_dumper:
            area_geo = shapely.geometry.shape(area['geometry'])
            if self.geo.intersects(area_geo):
                try:
                    intersection = self.geo.intersection(area_geo)
                except shapely.geos.TopologicalError:
                    intersection = self.geo.buffer(0).intersection(area_geo.buffer(0))
                if intersection.area/area_geo.area > 0.1:
                    yield area

class GeoClient(core.Client):
    @supported_years(2014, 2013, 2012, 2011, 2010, 2000)
    def geo_tract(self, fields, geojson_geometry, year=None):
        if year is None:
            year = self.default_year
        
        filtered_tracts = AreaFilter(geojson_geometry,
                                     GEO_URLS['tracts'][self.default_year])

        for tract in filtered_tracts:
            context = {'state' : tract['properties']['STATE'],
                       'county' : tract['properties']['COUNTY']}
            within = 'state:{state} county:{county}'.format(**context)

            tract_id = tract['properties']['TRACT']
            result = self.get(fields,
                              {'for': 'tract:{}'.format(tract_id),
                               'in' :  within}, year)

            if result:
                result, = result
            else:
                result = {}

            yield tract, result

    @supported_years(2014, 2013, 2012, 2011, 2010, 2000)
    def geo_blockgroup(self, fields, geojson_geometry, year=None):
        if year is None:
            year = self.default_year

        filtered_block_groups = AreaFilter(geojson_geometry,
                                           GEO_URLS['block groups'][year])

        for block_group in filtered_block_groups:
            context = {'state' : block_group['properties']['STATE'],
                       'county' : block_group['properties']['COUNTY'],
                       'tract' : block_group['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_group_id = block_group['properties']['BLKGRP']
            
            result = self.get(fields,
                              {'for': 'block group:{}'.format(block_group_id),
                               'in' :  within}, year)

            if result:
                result, = result
            else:
                result = {}

            yield block_group, result


    def _state_place_area(self, method, fields, state, place, year=None, return_geometry=False):
        if year is None:
            year = self.default_year
        
        search_query = "PLACE='{}' AND STATE={}".format(place, state)
        place_dumper = esridump.EsriDumper(GEO_URLS['incorporated places'][year],
                                           extra_query_args = {'where' : search_query,
                                                               'orderByFields': 'OID'})

        place = next(iter(place_dumper))
        logging.info(place['properties']['NAME'])
        place_geojson = place['geometry']

        areas = method(fields, place_geojson, year)

        features = []
        for i, (feature, result) in enumerate(areas):
            if return_geometry:
                feature['properties'].update(result)
                features.append(feature)
            else:
                features.append(result)
            if i % 100 == 0:
                logging.info('{} features'.format(i))

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features
                    
        
class ACS5Client(core.ACS5Client, GeoClient):

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2014, 2013, 2012, 2011, 2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

class SF1Client(core.SF1Client, GeoClient):
    @supported_years(2010, 2000, 1990)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2010, 2000)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

    @supported_years(2010, 2000)
    def state_place_block(self, *args, **kwargs):
        return self._state_place_area(self.geo_block, *args, **kwargs)

    @supported_years(2010, 2000)
    def geo_block(self, fields, geojson_geometry, year):
        if year is None:
            year = self.default_year
        
        filtered_blocks = AreaFilter(geojson_geometry,
                                     GEO_URLS['blocks'][year])

        for block in filtered_blocks:
            context = {'state' : block['properties']['STATE'],
                       'county' : block['properties']['COUNTY'],
                       'tract' : block['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_id = block['properties']['BLOCK']
            result = self.get(fields,
                              {'for': 'block:{}'.format(block_id),
                               'in' :  within}, year)

            if result:
                result, = result
            else:
                result = {}

            yield block, result


class SF3Client(core.SF3Client, GeoClient):
    @supported_years(2000, 1990)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2000)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

class Census(core.Census):
    def __init__(self, key, year=None, session=None):
        super(Census, self).__init__(key, year, session)
        self.acs5 = ACS5Client(key, year, session)
        self.sf1 = SF1Client(key, year, session)
        self.sf3 = SF3Client(key, year, session)
