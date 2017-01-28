#!/usr/bin/env python3

import botlib

from databot import define, task, this


cookies = {
    'incap_ses_473_791905': 'ufG9AaD4RXtatkliKG+QBrTFjFgAAAAATaho8h12YjOS7ZAL0Bmq1g==',
    'visid_incap_791905': '7Kok4JMCTYS2dfoJzIq6sFbja1cAAAAAQUIPAAAAAADogy7RIfk8/eiNbWGGzDHM',
}

pipeline = {
    'pipes': [
        define('pradžios-puslapiai', compress=True),
        define('sesijų-sąrašas'),
        define('sesijų-puslapiai', compress=True),
        define('posėdžių-sąrašas'),
        define('posėdžių-puslapiai', compress=True),
        define('klausimų-sąrašas'),
        define('klausimų-puslapiai', compress=True),
        define('balsavimų-sąrašas'),
        define('balsavimų-puslapiai', compress=True),
        define('registracijos-sąrašas'),
        define('registracijos-puslapiai', compress=True),
    ],
    'tasks': [
        # Pirmas puslapis
        task('pradžios-puslapiai').
        download('http://www.lrs.lt/sip/portal.show?p_r=15275&p_k=1', cookies=cookies),

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
        task('sesijų-sąrašas', 'sesijų-puslapiai').download(cookies=cookies),

        # Paskutinė sesija
        # Visada siunčiam paskutinę sisiją, kadangi ten gali būti naujų posėdžių.
        task('sesijų-sąrašas', 'sesijų-sąrašas').daily().max(this.value['pradžia']),
        task('sesijų-sąrašas', 'sesijų-puslapiai').download(cookies=cookies),

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
        ]).dedup(),
        task('posėdžių-sąrašas', 'posėdžių-puslapiai').download(cookies=cookies),

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
        ]).dedup(),
        task('klausimų-sąrašas', 'klausimų-puslapiai').download(cookies=cookies),

        # Balsavimų sąrašas
        task('klausimų-puslapiai', 'balsavimų-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="balsavimas"]', '@href'
        ]).dedup(),
        task('balsavimų-sąrašas', 'balsavimų-puslapiai').download(cookies=cookies),

        # Balsavimo rezultatai
        task('balsavimų-puslapiai', 'registracijos-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="registracija"]', '@href'
        ]).dedup(),

        # Registracijos puslapiai
        task('registracijos-sąrašas', 'registracijos-puslapiai').download(cookies=cookies),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
