#!/usr/bin/env python3

import botlib

from datetime import timedelta
from databot import row, strip


def define(bot):
    bot.define('index urls')
    bot.define('index pages')
    bot.define('dataset urls')
    bot.define('dataset pages')
    bot.define('dataset data')
    bot.define('datasets')


def run(bot):

    start_url = 'http://opendata.gov.lt/index.php?vars=/public/public/search'
    with bot.pipe('index urls').clean(timedelta(days=1)).append(start_url).dedup():
        while bot.pipe('index pages').is_filled():
            with bot.pipe('index pages').download():
                bot.pipe('index urls').select(['td > a.path@href']).dedup()

    with bot.pipe('index pages'):
        bot.pipe('dataset urls').reset().select(['form[name=frm] > table > tr > td[3] > a@href'])

    with bot.pipe('dataset urls').clean(timedelta(days=7)).dedup():
        with bot.pipe('dataset pages').download():
            bot.pipe('dataset data').select(row.key, [
                'table xpath:tr[count(td)=2]', (
                    'td[1]:content',
                    strip('td[2]:content'),
                )
            ])

    with bot.pipe('dataset data').clean(timedelta(days=7)).dedup():
        bot.pipe('datasets').call(lambda x: [(x.key, dict(x.value))])

    bot.compact()

    bot.pipe('datasets').export('data/ivpk/opendata-gov-lt/datasets.csv')


if __name__ == '__main__':
    botlib.runbot(define, run)
