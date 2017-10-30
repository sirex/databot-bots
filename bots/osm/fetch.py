#!/usr/bin/env python3

import pathlib
import funcy
import subprocess
import shutil
import psycopg2
import contextlib
import logging


logger = logging.getLogger(__name__)


def main():
    """

    Install system packages:

        postgresql postgis osm2pgsql

    """
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

    assert shutil.which('osm2pgsql'), 'install osm2pgsql'

    dbname = 'lietuva'
    database_created = False
    with contextlib.closing(psycopg2.connect('postgresql:///postgres')) as conn:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        with contextlib.closing(conn.cursor()) as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM pg_database WHERE datname=%s)", (dbname,))
            exists, = cur.fetchone()
            if not exists:
                logger.info("create database %s", dbname)
                cur.execute('CREATE DATABASE ' + dbname)
                database_created = True

    if database_created:
        with contextlib.closing(psycopg2.connect('postgresql:///' + dbname)) as conn:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            with contextlib.closing(conn.cursor()) as cur:
                logger.info("create extension postgis")
                cur.execute('CREATE EXTENSION postgis;')

    code = pathlib.Path('bots/osm')
    data = pathlib.Path('data/osm')
    output = data / 'LT.tar.gz2'
    source = 'http://download.gisgraphy.com/openstreetmap/pbf/LT.tar.bz2'

    logger.info('downloading %s', source)
    http_code = subprocess.run(funcy.flatten([
        'curl', source,
        ['--time-cond', str(output)] if output.exists() else [],
        '--output', str(output),
        '--location',
        '--silent',
        '--write-out', '%{http_code}',
    ]), check=True, stdout=subprocess.PIPE).stdout

    http_code = http_code.decode()
    logger.info('http code: %s', http_code)

    if http_code == '200':
        logger.info('extracting %s', output)
        subprocess.run(['tar', '--directory', str(output.parent), '-xjf', str(output)], check=True)

        logger.info('importing %s', data / 'LT')
        # https://github.com/openstreetmap/osm2pgsql#usage
        subprocess.run([
            'osm2pgsql',
            '--create',
            '--database', dbname,
            '--style', str(code / 'lietuva.style'),
            '--input-reader', 'pbf',
            str(data / 'LT'),
        ], check=True)

    logger.info('done')


if __name__ == "__main__":
    main()
