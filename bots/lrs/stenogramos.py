#!/usr/bin/env python3

import botlib

from databot import this, select


def define(bot):
    bot.define('posėdžių-puslapiai', botlib.dburi('lrs/balsavimai'))
    bot.define('stenogramų-sąrašas')
    bot.define('stenogramų-puslapiai')
    bot.define('metadata')


def run(bot):
    with bot.pipe('posėdžių-puslapiai'):
        with bot.pipe('stenogramų-sąrašas').select(['.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href']).dedup():
            bot.pipe('stenogramų-puslapiai').download()

    with bot.pipe('stenogramų-puslapiai'):
        bot.pipe('metadata').select(this.key, select([
            '.basic .ltb',
            (select(':text').strip(), select('b:text?').strip()),
        ]).cast(dict)).dedup()

    bot.pipe('metadata').export('data/lrs/stenogramos/metadata.csv', include=[
        'key',
        'Data:',
        'Rūšis:',
        'Kalba:',
        'Numeris:',
    ])

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
