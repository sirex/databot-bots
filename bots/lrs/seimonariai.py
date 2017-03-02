#!/usr/bin/env python3

import os
import botlib

from itertools import groupby
from operator import itemgetter

from databot import define, select, task, this


def case_split(value):
    words = [(w.isupper(), w) for w in value.split()]
    return [' '.join([x for _, x in g]) for k, g in groupby(words, key=itemgetter(0))]


envvars = {'incap_ses_108_791905', 'incap_ses_473_791905'}
cookies = {x: os.environ[x] for x in envvars if x in os.environ}

pipeline = {
    'pipes': [
        define('1990/sąrašas-puslapiai', compress=True),
        define('1990/sąrašas-duomenys'),
        define('2016/sąrašas-puslapiai', compress=True),
        define('2016/sąrašas-duomenys'),
        define('2016/nuotraukos'),
    ],
    'tasks': [
        task('1990/sąrašas-puslapiai').monthly().download('http://www3.lrs.lt/pls/inter/w5_lrs.seimo_nariu_sarasas?p_kade_id=1'),
        task('1990/sąrašas-puslapiai', '1990/sąrašas-duomenys').select([
            'xpath://td[h1/h2/text()="Seimo narių sąrašas"]/ol/li[count(a)=1]/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        task('pirmas-puslapis').monthly().download(
            'http://www.lrs.lt/sip/portal.show?p_r=8801&p_k=1&filtertype=0', cookies=cookies, check='.smn-list',
        ),

        task('pirmas-puslapis').monthly().
            download('http://www.lrs.lt/sip/portal.show?p_r=8801&p_k=1&filtertype=0', cookies=cookies).
            dtype('content:html', has='.smn-list'),

        # Seimo narių sąrašas
        task('pirmas-puslapis', 'sąrašas').select([
            '.smn-list .list-member', (
                'a.smn-name@href', {
                    'vardas': select('a.smn-name:text'),
                    'pavarde': select('a.smn-name > span.smn-pavarde:text'),
                    'nuotrauka': select('.smn-big-photo img@src'),
                },
            ),
        ]),

        # Nuotraukos
        task('sąrašas', 'nuotraukos').
            download(this.value.nuotrauka, cookies=cookies).
            dtype('content:image').
            dtype('oneof', [
                dtype('content:image'),
                dtype('content:html', check=this.headers['Content-Type'] == 'text/html'),
            ])
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
