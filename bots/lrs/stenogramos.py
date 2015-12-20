#!/usr/bin/env python3

import botlib


def define(bot):
    bot.define('posėdžių-puslapiai', botlib.dburi('lrs/balsavimai'))
    bot.define('stenogramų-sąrašas')
    bot.define('stenogramų-puslapiai')
    # bot.define('klausimų-puslapiai')
    # bot.define('balsavimų-sąrašas')
    # bot.define('balsavimų-puslapiai')
    # bot.define('registracijos-sąrašas')
    # bot.define('registracijos-puslapiai')


def run(bot):
    with bot.pipe('posėdžių-puslapiai'):
        with bot.pipe('stenogramų-sąrašas').select([
            '.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href'
        ]).dedup():
            bot.pipe('stenogramų-puslapiai').download()


if __name__ == '__main__':
    botlib.runbot(define, run)
