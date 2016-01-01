#!/usr/bin/env python3

import botlib


def define(bot):
    bot.define('klausimų-puslapiai', botlib.dburi('lrs/balsavimai'))
    bot.define('dokumentų-sąrašas')
    bot.define('dokumentų-puslapiai')
    bot.define('susijusių-dokumentų-sąrašas')
    bot.define('susijusių-dokumentų-puslapiai')
    # bot.define('klausimų-puslapiai')
    # bot.define('balsavimų-sąrašas')
    # bot.define('balsavimų-puslapiai')
    # bot.define('registracijos-sąrašas')
    # bot.define('registracijos-puslapiai')


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


if __name__ == '__main__':
    botlib.runbot(define, run)
