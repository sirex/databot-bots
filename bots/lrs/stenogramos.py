#!/usr/bin/env python3

import botlib

from databot import define, select, task


pipeline = {
    'pipes': [
        define('posėdžių-puslapiai', botlib.dburi('lrs/balsavimai')),
        define('stenogramų-sąrašas'),
        define('stenogramų-puslapiai'),
        define('metadata'),
    ],
    'tasks': [
        task('posėdžių-puslapiai', 'stenogramų-sąrašas').select(
            '.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href'
        ).dedup(),
        task('stenogramų-sąrašas', 'stenogramų-puslapiai').download(),
        task('stenogramų-puslapiai', 'metadata').select([
            '.basic .ltb', (
                select(':text').strip(),
                select('b:text?').strip(),
            )
        ]),
        task('metadata').export('data/lrs/stenogramos/metadata.csv', include=[
            'key',
            'Data:',
            'Rūšis:',
            'Kalba:',
            'Numeris:',
        ]),
        task().compact(),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
