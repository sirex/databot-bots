#!/usr/bin/env python3

import botlib


def define(bot):
    bot.define('pradžios-nuorodos')
    bot.define('pradžios-puslapiai')
    bot.define('sesijų-sąrašas')
    bot.define('sesijų-puslapiai')
    bot.define('posėdžių-sąrašas')
    bot.define('posėdžių-puslapiai')
    bot.define('klausimų-sąrašas')
    bot.define('klausimų-puslapiai')
    # bot.define('svarstymai')
    # bot.define('registracijų-nuorodos')
    # bot.define('balsavimų-nuorodos')
    # bot.define('registracijų-puslapiai')
    # bot.define('balsavimų-puslapiai')
    # bot.define('registracijos')
    # bot.define('balsavimai')


def run(bot):

    start_urls = [
        'http://www.lrs.lt/sip/portal.show?p_r=15275&p_k=1',
    ]

    with bot.pipe('pradžios-nuorodos').append(start_urls).dedup():
        bot.pipe('pradžios-puslapiai').download()

    with bot.pipe('pradžios-puslapiai').dedup():
        bot.pipe('sesijų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[1] > a.link@href', {
                    'url': 'td[1] > a.link@href',
                    'pavadinimas': 'td[1] > a.link:text',
                    'pradžia': 'td[2]:text',
                    'pabaiga': 'td[3]:text',
                },
            ),
        ])

    with bot.pipe('sesijų-sąrašas').dedup():
        bot.pipe('sesijų-puslapiai').download()

    with bot.pipe('sesijų-puslapiai').dedup():
        bot.pipe('posėdžių-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=4]/td[2]/a', (
                '@href', {
                    'url': '@href',
                    'tipas': ':text',
                    'data': 'xpath:../../td[1]/a/text()',
                    'darbotvarkė': 'xpath:../../td[3]/a/@href',
                    'priimti projektai': 'xpath:../../td[4]/a/@href',
                },
            ),
        ])

    with bot.pipe('posėdžių-sąrašas').dedup():
        bot.pipe('posėdžių-puslapiai').download()

    with bot.pipe('posėdžių-puslapiai').dedup():
        bot.pipe('klausimų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[3] > a@href', {
                    'url': 'td[3] > a@href',
                    'laikas': 'td[1]:text',
                    'numeris': 'td[2]:text',
                    'klausimas': 'td[3] > a:text',
                    'tipas': 'xpath:td[3]/text()?',
                },
            ),
        ])

    with bot.pipe('klausimų-sąrašas').dedup():
        bot.pipe('klausimų-puslapiai').download()

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
