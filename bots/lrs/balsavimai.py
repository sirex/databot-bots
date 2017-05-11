#!/usr/bin/env python3

import yaml
import botlib

from databot import define, task, this, select


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']['www.lrs.lt']

pipeline = {
    'pipes': [
        define('klausimų-puslapiai', botlib.dburi('lrs/posedziai')),
        define('balsavimų-sąrašas'),
        define('balsavimų-puslapiai', compress=True),
        define('balsavimų-duomenys'),
        define('registracijos-sąrašas'),
        define('registracijos-puslapiai', compress=True),
    ],
    'tasks': [
        # Darbotvarkės klausimas (balsavimai)
        task('klausimų-puslapiai', 'balsavimų-sąrašas').
        select(
            ['.sale_svarst_eiga tr td[2] xpath:a[text()="balsavimas"]', '@href'],
            check='xpath://h1[contains(text(), "Darbotvarkės klausimas")]/text()',
        ).
        dedup(),

        task('balsavimų-sąrašas', 'balsavimų-puslapiai').
        download(cookies=cookies, check='#page-content h1.page-title'),

        task('balsavimų-puslapiai', 'balsavimų-duomenys').
        select(this.key, {
            'data': select('.page-title:text').re(r'\d{4}-\d{2}-\d{2}'),
            'posėdis': select('.page-title:text').re(r'(\w+) posėdis\)'),
            'klausimai': ['xpath://b/a[contains(@class, "link") and text()="dokumento tekstas"]', {
                'pavadinimas': select('xpath:./../preceding-sibling::b[contains(a/@class, "link")][1]/a/text()[1]'),
                'rūšis': select('xpath:./../preceding-sibling::b[contains(a/@class, "link")][1]/following-sibling::text()[1]'),
                'klausimo-nuoroda': select('xpath:./../preceding-sibling::b[contains(a/@class, "link")][1]/a/@href'),
                'dokumento-nuoroda': select('@href'),
            }],
            'formuluotė': select('#page-content .default xpath://text()[.="Formuluotė: "]/following-sibling::b[1]/text()?'),
            'laikas': select('#page-content .default xpath://text()[.="Balsavimo laikas: "]/following-sibling::b[1]/text()'),
            'balsavo-seimo-narių': select('#page-content .default xpath://text()[.="Balsavo Seimo narių: "]/following-sibling::b[1]/text()'),
            'viso-seimo-narių': select('#page-content .default xpath://text()[.="Balsavo Seimo narių: "]/following-sibling::text()[.=" iš "][1]/following-sibling::b[1]/text()'),
            'rezultatai': ['.sale-group-title xpath:text()[.="Individualūs balsavimo  rezultatai"]/../following-sibling::table/tr[count(td)=5]', {
                'vardas': select('td[1] > a:text'),
                'seimo-nario-nuoroda': select('td[1] > a@href'),
                'p_asm_id': select('td[1] > a@href').re('p_asm_id=(-?\d+)').cast(int),
                'frakcija': select('td[2]:text'),
                'už': select('td[3]:text'),
                'prieš': select('td[4]:text'),
                'susilaikė': select('td[5]:text'),
            }]
        }).
        dedup(),

        # Darbotvarkės klausimas (registracijos)
        task('klausimų-puslapiai', 'registracijos-sąrašas').
        select(
            ['.sale_svarst_eiga tr td[2] xpath:a[text()="registracija"]', '@href'],
            check='xpath://h1[contains(text(), "Darbotvarkės klausimas")]/text()',
        ).
        dedup(),

        task('registracijos-sąrašas', 'registracijos-puslapiai').
        download(cookies=cookies, check='#page-content h1.page-title'),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
