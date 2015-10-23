#!/usr/bin/env python3

import botlib
import unicodedata

from databot import call, subst


def strip_accents(string, accents=('COMBINING ACUTE ACCENT', 'COMBINING GRAVE ACCENT', 'COMBINING TILDE')):
    accents = set(map(unicodedata.lookup, accents))
    chars = [c for c in unicodedata.normalize('NFD', string) if c not in accents]
    return unicodedata.normalize('NFC', ''.join(chars))


def define(bot):
    bot.define('titulinio nuoroda')
    bot.define('titulinis')
    bot.define('puslapių nuorodos')
    bot.define('sąrašų puslapiai')
    bot.define('vardų sąrašas')
    bot.define('vardų puslapiai')


def run(bot):
    start_url = 'http://vardai.vlkk.lt/'

    with bot.pipe('titulinio nuoroda').append(start_url).dedup():
        with bot.pipe('titulinis').download():
            with bot.pipe('puslapių nuorodos').select(['#siteMenu > li > a', ('@href', ':text')]).dedup():
                with bot.pipe('sąrašų puslapiai').download():
                    bot.pipe('vardų sąrašas').select([
                        'ul.namesList xpath:.//li/a[contains(@class, "Name")]', (
                            '@href', {
                                'gender': subst('@class', {'fName': 'f', 'mName': 'm'}),
                                'name': call(strip_accents, ':text'),
                            }
                        )
                    ]).dedup()

    # with bot.pipe('vardų sąrašas'):
    #     bot.pipe('vardų puslapiai').download()

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
