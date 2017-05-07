#!/usr/bin/env python3

import yaml
import botlib

from databot import define, task


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']['www.lrs.lt']

pipeline = {
    'pipes': [
        define('klausimų-puslapiai', botlib.dburi('lrs/posedziai')),
        define('balsavimų-sąrašas'),
        define('balsavimų-puslapiai', compress=True),
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
