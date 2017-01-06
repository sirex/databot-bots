#!/usr/bin/env python3

import botlib


def define(bot):
    bot.define('pradžios-nuorodos')
    bot.define('pradžios-puslapiai', compress=True)
    bot.define('sesijų-sąrašas')
    bot.define('sesijų-puslapiai', compress=True)
    bot.define('posėdžių-sąrašas')
    bot.define('posėdžių-puslapiai', compress=True)
    bot.define('klausimų-sąrašas')
    bot.define('klausimų-puslapiai', compress=True)
    bot.define('balsavimų-sąrašas')
    bot.define('balsavimų-puslapiai', compress=True)
    bot.define('registracijos-sąrašas')
    bot.define('registracijos-puslapiai', compress=True)


def run(bot):
    cookies = {
        'incap_ses_473_791905': 'Jb8dGqFDdxX6QoB+BW+QBhiQB1gAAAAANmzNwNFdVgbtgumFNyY5QA==',
    }

    bot.pipe('pradžios-puslapiai').download('http://www.lrs.lt/sip/portal.show?p_r=15275&p_k=1', cookies=cookies)

    # Always download last session page to get all new sessions
    for key, value in sorted(bot.pipe('sesijų-sąrašas').data.items(), key=lambda x: x[1]['pradžia'], reverse=True):
        bot.pipe('sesijų-sąrašas').append(key, value).compact()
        break

    with bot.pipe('pradžios-puslapiai'):
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
        bot.pipe('sesijų-puslapiai').download(cookies=cookies)

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
            bot.pipe('posėdžių-puslapiai').download(cookies=cookies)

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
            bot.pipe('klausimų-puslapiai').download(cookies=cookies)

    with bot.pipe('klausimų-puslapiai').dedup():
        with bot.pipe('balsavimų-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="balsavimas"]', '@href'
        ]).dedup():
            bot.pipe('balsavimų-puslapiai').download(cookies=cookies)

    with bot.pipe('klausimų-puslapiai').dedup():
        with bot.pipe('registracijos-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="registracija"]', '@href'
        ]).dedup():
            bot.pipe('registracijos-puslapiai').download(cookies=cookies)

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
