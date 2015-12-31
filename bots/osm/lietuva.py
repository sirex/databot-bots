#!/usr/bin/env python3

import pathlib
import funcy
import botlib
import subprocess
import sqlalchemy as sa
import geoalchemy2  # noqa


def query_places():
    engine = sa.create_engine('postgresql:///lietuva')
    metadata = sa.MetaData()
    point = sa.Table('planet_osm_point', metadata, autoload=True, autoload_with=engine).alias('point')
    polygon = sa.Table('planet_osm_polygon', metadata, autoload=True, autoload_with=engine).alias('polygon')

    conn = engine.connect()

    place_types = ['city', 'suburb', 'town', 'hamlet', 'village']

    srid = 4326  # http://spatialreference.org/ref/epsg/4326/

    query = (
        sa.select([
            point.c.osm_id,
            point.c.place,
            point.c.name,
            point.c.population,
            sa.func.ST_X(sa.func.ST_Transform(point.c.way, srid)).label('point_lon'),
            sa.func.ST_Y(sa.func.ST_Transform(point.c.way, srid)).label('point_lat'),
            polygon.c.osm_id,
            polygon.c.name,
            polygon.c.admin_level,
        ], use_labels=True).
        where(sa.and_(
            point.c.place.in_(place_types),
            polygon.c.boundary == 'administrative',
            polygon.c.admin_level.in_([
                '4',  # apskritis
                '5',  # rajonas
                '6',  # seniūnija
            ]),
            sa.func.ST_Contains(polygon.c.way, point.c.way)
        )).
        order_by(point.c.osm_id)
    )

    data = {}

    for row in conn.execute(query):
        if data and row.point_osm_id != data['osm_id']:
            yield data['osm_id'], data
            data = {}

        data.update({
            'osm_id': row.point_osm_id,
            'type': row.point_place,
            'place': row.point_name,
            'lon': row.point_lon,
            'lat': row.point_lat,
            'population': row.point_population,
            'admin_level_%s' % row.polygon_admin_level: row.polygon_name,
            'admin_level_%s_osm_id' % row.polygon_admin_level: row.polygon_osm_id,
        })

    if data:
        yield data['osm_id'], data


def define(bot):
    bot.define('places')


def run(bot):
    source = 'http://download.gisgraphy.com/openstreetmap/pbf/LT.tar.bz2'
    output = pathlib.Path('data/osm/LT.tar.gz2')

    bot.output.info('Downloading %s' % source)
    http_code = subprocess.check_output(funcy.flatten([
        'curl', source,
        ['--time-cond', str(output)] if output.exists() else [],
        '--output', str(output),
        '--location',
        '--silent',
        '--write-out', '%{http_code}',
    ]))

    http_code = http_code.decode()

    if http_code == '200':
        bot.output.info('Extracting %s' % output)
        subprocess.check_call(['tar', '--directory', str(output.parent), '-xjf', str(output)])

    bot.output.info('Query places')
    bot.pipe('places').clean().append(query_places(), progress='places')

    bot.output.info('Export places to %s' % output.with_name('places.csv'))
    bot.pipe('places').export(str(output.with_name('places.csv')), include=[
        'osm_id',
        'type',
        'place',
        'population',
        'lon',
        'lat',
        'admin_level_6_osm_id',
        'admin_level_6',
        'admin_level_5_osm_id',
        'admin_level_5',
        'admin_level_4_osm_id',
        'admin_level_4',
    ])

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
