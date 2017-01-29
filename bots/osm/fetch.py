#!/usr/bin/env python3

import pathlib
import funcy
import subprocess
import shutil


def main():
    """

    Install system packages:

        sudo apt install postgresql postgis osm2pgsql

    Don't forget to create the database:

        createdb --encoding='utf-8' --locale=lt_LT.UTF-8 --template=template0 lietuva
        psql -c 'CREATE EXTENSION postgis;' lietuva

    """

    assert shutil.which('osm2pgsql'), 'sudo apt install osm2pgsql'

    code = pathlib.Path('bots/osm')
    data = pathlib.Path('data/osm')
    output = data / 'LT.tar.gz2'
    source = 'http://download.gisgraphy.com/openstreetmap/pbf/LT.tar.bz2'

    print('Downloading %s' % source)
    http_code = subprocess.run(funcy.flatten([
        'curl', source,
        ['--time-cond', str(output)] if output.exists() else [],
        '--output', str(output),
        '--location',
        '--silent',
        '--write-out', '%{http_code}',
    ]), check=True, stdout=subprocess.PIPE).stdout

    http_code = http_code.decode()

    if True or http_code == '200':
        print('Extracting %s' % output)
        # subprocess.run(['tar', '--directory', str(output.parent), '-xjf', str(output)], check=True)

        print('Importing %s' % (data / 'LT'))
        # https://github.com/openstreetmap/osm2pgsql#usage
        subprocess.run([
            'osm2pgsql',
            '--create',
            '--database', 'lietuva',
            '--style', str(code / 'lietuva.style'),
            '--input-reader', 'pbf',
            str(data / 'LT'),
        ], check=True)


if __name__ == "__main__":
    main()
