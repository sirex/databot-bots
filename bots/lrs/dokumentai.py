#!/usr/bin/env python3

import botlib

from databot import row, call, strip


def define(bot):
    bot.define('klausimų-puslapiai', botlib.dburi('lrs/balsavimai'))
    bot.define('dokumentų-sąrašas')
    bot.define('dokumentų-puslapiai')
    bot.define('susijusių-dokumentų-sąrašas')
    bot.define('susijusių-dokumentų-puslapiai')
    bot.define('metadata')


def run(bot):
    with bot.pipe('klausimų-puslapiai'):
        with bot.pipe('dokumentų-sąrašas').select([
            '#page-content div.default b xpath:a[text()="dokumento tekstas"]/@href'
        ]).dedup():
            bot.pipe('dokumentų-puslapiai').download()

        with bot.pipe('susijusių-dokumentų-sąrašas').select([
            '#page-content div.default b xpath:a[text()="susiję dokumentai"]/@href'
        ]).dedup():
            bot.pipe('susijusių-dokumentų-puslapiai').download()

    with bot.pipe('dokumentų-puslapiai'):
        bot.pipe('metadata').select(row.key, call(dict, ['.basic .ltb', (strip(':text'), strip('b:text?'))])).dedup()

    bot.pipe('metadata').export('data/lrs/dokumentai/metadata.csv', include=[
        'key',
        'Data:',
        'Rūšis:',
        'Kalba:',
        'Numeris:',
        'Statusas:',
    ])

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
