#!/usr/bin/env python3

import botlib
import sqlalchemy as sa
import geoalchemy2  # noqa

from databot import define, task

# http://spatialreference.org/ref/epsg/4326/
WGS84 = 4326

# http://wiki.openstreetmap.org/wiki/EPSG:3857
EPSG3857 = 900913


def make_point(lon, lat):
    point = sa.func.ST_MakePoint(lon, lat)
    return sa.func.ST_Transform(sa.func.ST_SetSRID(point, WGS84), EPSG3857)


def find_closes_place(conn, point, row):
    place_types = ['city', 'town', 'hamlet', 'village']

    within = 10000  # within distance in meters
    distance = sa.func.ST_Distance(point.c.way, make_point(row.lon, row.lat)).label('distance')

    query = (
        sa.select([
            point.c.osm_id,
            point.c.place,
            point.c.name,
            point.c.population,
            sa.func.ST_X(sa.func.ST_Transform(point.c.way, WGS84)).label('lon'),
            sa.func.ST_Y(sa.func.ST_Transform(point.c.way, WGS84)).label('lat'),
            distance,
        ]).
        where(sa.and_(
            point.c.place.in_(place_types),
            sa.func.ST_DWithin(point.c.way, make_point(row.lon, row.lat), within),
        )).
        order_by(distance)
    )

    for i, x in enumerate(conn.execute(query)):
        return {
            'osm_id': x.osm_id,
            'name': x.name,
            'lon': x.lon,
            'lat': x.lat,
            'population': x.population,
            'distance': x.distance,
        }


def query():
    engine = sa.create_engine('postgresql:///lietuva')
    metadata = sa.MetaData()
    point = sa.Table('planet_osm_point', metadata, autoload=True, autoload_with=engine).alias('point')
    polygon = sa.Table('planet_osm_polygon', metadata, autoload=True, autoload_with=engine).alias('polygon')

    conn = engine.connect()

    queries = [
        (
            sa.select([
                point.c.osm_id,
                point.c.name,
                point.c.religion,
                point.c.denomination,
                sa.func.ST_X(sa.func.ST_Transform(point.c.way, WGS84)).label('lon'),
                sa.func.ST_Y(sa.func.ST_Transform(point.c.way, WGS84)).label('lat'),
            ]).
            where(sa.and_(
                point.c.amenity == 'place_of_worship',
            )).
            order_by(point.c.osm_id)
        ),
        (
            sa.select([
                polygon.c.osm_id,
                polygon.c.name,
                polygon.c.religion,
                polygon.c.denomination,
                sa.func.ST_X(sa.func.ST_Transform(sa.func.ST_Centroid(polygon.c.way), WGS84)).label('lon'),
                sa.func.ST_Y(sa.func.ST_Transform(sa.func.ST_Centroid(polygon.c.way), WGS84)).label('lat'),
            ]).
            where(sa.and_(
                polygon.c.amenity == 'place_of_worship',
            )).
            order_by(polygon.c.osm_id)
        ),
    ]

    for qry in queries:
        for row in conn.execute(qry):
            yield row.osm_id, {
                'osm_id': row.osm_id,
                'name': row.name,
                'lon': row.lon,
                'lat': row.lat,
                'religion': row.religion,
                'denomination': row.denomination,
                'place': find_closes_place(conn, point, row),
            }


pipeline = {
    'pipes': [
        define('baznycios'),
    ],
    'tasks': [
        task('baznycios').once().clean().append(query(), progress='baznycios').compact(),
        task('baznycios').once().export('data/osm/baznycios.csv', include=[
            'osm_id',
            'name',
            'religion',
            'denomination',
            'lon',
            'lat',
            'place.osm_id',
            'place.name',
            'place.distance',
            'place.population',
            'place.lon',
            'place.lat',
        ])
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
