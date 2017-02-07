#!/usr/bin/env python3

import os
import botlib

from databot import define, task


cookies = {
    'incap_ses_473_791905': os.environ['INCAP_SES'],
}

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
        task('klausimų-puslapiai', 'balsavimų-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="balsavimas"]', '@href'
        ], check='xpath://h1[contains(text(), "Darbotvarkės klausimas")]/text()').dedup(),
        task('balsavimų-sąrašas', 'balsavimų-puslapiai').download(cookies=cookies),

        # Darbotvarkės klausimas (registracijos)
        task('klausimų-puslapiai', 'registracijos-sąrašas').select([
            '.sale_svarst_eiga tr td[2] xpath:a[text()="registracija"]', '@href'
        ], check='xpath://h1[contains(text(), "Darbotvarkės klausimas")]/text()').dedup(),
        task('registracijos-sąrašas', 'registracijos-puslapiai').download(cookies=cookies),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
