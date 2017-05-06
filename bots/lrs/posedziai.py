#!/usr/bin/env python3

import yaml
import botlib

from databot import define, task, this


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']['www.lrs.lt']

pipeline = {
    'pipes': [
        define('pradžios-puslapiai', compress=True),
        define('sesijų-sąrašas'),
        define('sesijų-puslapiai', compress=True),
        define('posėdžių-sąrašas'),
        define('posėdžių-puslapiai', compress=True),
        define('klausimų-sąrašas'),
        define('klausimų-puslapiai', compress=True),
    ],
    'tasks': [
        # Pirmas puslapis
        task('pradžios-puslapiai').daily().download(
            'http://www.lrs.lt/sip/portal.show?p_r=15275&p_k=1', cookies=cookies, check='#page-content h1.page-title'
        ),

        # Sesijų sąrašas
        task('pradžios-puslapiai', 'sesijų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[1] > a.link@href', {
                    'url': 'td[1] > a.link@href',
                    'pavadinimas': 'td[1] > a.link:text',
                    'pradžia': 'td[2]:text',
                    'pabaiga': 'td[3]:text',
                },
            ),
        ]).dedup(),
        task('sesijų-sąrašas', 'sesijų-puslapiai').download(cookies=cookies, check='#page-content h1.page-title'),

        # Paskutinė sesija
        # Visada siunčiam paskutinę sisiją, kadangi ten gali būti naujų posėdžių.
        task('sesijų-sąrašas', 'sesijų-sąrašas').daily().max(this.value['pradžia']),
        task('sesijų-sąrašas', 'sesijų-puslapiai').download(cookies=cookies, check='#page-content h1.page-title'),

        # Posėdžių sąrašas
        task('sesijų-puslapiai', 'posėdžių-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=4]/td[2]/a', (
                '@href', {
                    'url': '@href',
                    'tipas': ':text',
                    'data': 'xpath:../../td[1]/a/text()',
                    'darbotvarkė': 'xpath:../../td[3]/a/@href',
                    'priimti projektai': 'xpath:../../td[4]/a/@href',
                },
            ),
        ], check='#page-content h1.page-title').dedup(),
        task('posėdžių-sąrašas', 'posėdžių-puslapiai').download(cookies=cookies, check='#page-content h1.page-title'),

        # Svarstytų klausimų sąrašas
        task('posėdžių-puslapiai', 'klausimų-sąrašas').select([
            '#page-content .tbl-default xpath:tr[count(td)=3]', (
                'td[3] > a@href', {
                    'url': 'td[3] > a@href',
                    'laikas': 'td[1]:text',
                    'numeris': 'td[2]:text',
                    'klausimas': 'td[3] > a:text',
                    'tipas': 'xpath:td[3]/text()?',
                },
            ),
        ], check='.fakt_pos > .list.main li > a').dedup(),
        task('klausimų-sąrašas', 'klausimų-puslapiai').download(cookies=cookies, check='#page-content h1.page-title'),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
