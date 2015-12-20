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
    bot.define('balsavimų-sąrašas')
    bot.define('balsavimų-puslapiai')
    bot.define('registracijos-sąrašas')
    bot.define('registracijos-puslapiai')


def run(bot):

    start_urls = [
        'http://www.lrs.lt/sip/portal.show?p_r=15275&p_k=1',
    ]

    with bot.pipe('pradžios-nuorodos').append(start_urls):
        bot.pipe('pradžios-puslapiai').download()

    # Always download last session page to get all new sessions
    for key, value in sorted(bot.pipe('sesijų-sąrašas').data.items(), key=lambda x: x[1]['pradžia'], reverse=True):
        bot.pipe('sesijų-sąrašas').append(key, value).compact()
        break

    with bot.pipe('pradžios-puslapiai'):
        with bot.pipe('sesijų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[1] > a.link@href', {
                    'url': 'td[1] > a.link@href',
                    'pavadinimas': 'td[1] > a.link:text',
                    'pradžia': 'td[2]:text',
                    'pabaiga': 'td[3]:text',
                },
            ),
        ]).dedup():
            bot.pipe('sesijų-puslapiai').download()

    with bot.pipe('sesijų-puslapiai'):
        with bot.pipe('posėdžių-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=4]/td[2]/a', (
                '@href', {
                    'url': '@href',
                    'tipas': ':text',
                    'data': 'xpath:../../td[1]/a/text()',
                    'darbotvarkė': 'xpath:../../td[3]/a/@href',
                    'priimti projektai': 'xpath:../../td[4]/a/@href',
                },
            ),
        ]).dedup():
            bot.pipe('posėdžių-puslapiai').download()

    with bot.pipe('posėdžių-puslapiai').dedup():
        with bot.pipe('klausimų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[3] > a@href', {
                    'url': 'td[3] > a@href',
                    'laikas': 'td[1]:text',
                    'numeris': 'td[2]:text',
                    'klausimas': 'td[3] > a:text',
                    'tipas': 'xpath:td[3]/text()?',
                },
            ),
        ]).dedup():
            bot.pipe('klausimų-puslapiai').download()

    with bot.pipe('klausimų-puslapiai').dedup():
        with bot.pipe('balsavimų-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="balsavimas"]', '@href'
        ]).dedup():
            bot.pipe('balsavimų-puslapiai').download()

    with bot.pipe('klausimų-puslapiai').dedup():
        with bot.pipe('registracijos-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="registracija"]', '@href'
        ]).dedup():
            bot.pipe('registracijos-puslapiai').download()

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
