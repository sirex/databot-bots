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
    bot.define('texts')


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

    with bot.pipe('dokumentų-puslapiai'):
        bot.pipe('texts').select(row.key, 'body > div:content').dedup()

    bot.pipe('metadata').export('data/lrs/dokumentai/metadata.csv', include=[
        'key',
        'Data:',
        'Rūšis:',
        'Kalba:',
        'Numeris:',
        'Statusas:',
    ])

    bot.pipe('texts').export('data/lrs/dokumentai/texts.csv', include=[
        'key',
        'value',
    ])

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
