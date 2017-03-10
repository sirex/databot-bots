#!/usr/bin/env python3

import yaml
import botlib

from itertools import groupby
from operator import itemgetter

from databot import define, select, task, this, func, join


def case_split(value):
    words = [(w.isupper(), w) for w in value.split()]
    return [' '.join([x for _, x in g]) for k, g in groupby(words, key=itemgetter(0))]


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']

pipeline = {
    'pipes': [
        define('1990/sąrašo-puslapis', compress=True),
        define('1990/sąrašo-duomenys'),
        define('1990/seimo-nario-puslapis', compress=True),
        define('1990/seimo-nario-duomenys'),
        define('1990/seimo-nario-nuotrauka'),

        define('2016/sąrašo-puslapis', compress=True),
        define('2016/sąrašo-duomenys'),
        define('2016/seimo-nario-nuotrauka'),
    ],
    'tasks': [
        # 1990 kadencija
        # ==============

        # Seimo narių sąrašas
        task('1990/sąrašo-puslapis').monthly().
        download('http://www3.lrs.lt/pls/inter/w5_lrs.seimo_nariu_sarasas?p_kade_id=1',
                 cookies=cookies['www3.lrs.lt']),

        task('1990/sąrašo-puslapis', '1990/sąrašo-duomenys').select([
            'xpath://td[h1/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        # Seimo narių puslapiai
        task('1990/sąrašo-duomenys', '1990/seimo-nario-puslapis').
        download(cookies=cookies['www3.lrs.lt'], check='#SN_pareigos'),

        task('1990/seimo-nario-puslapis', '1990/seimo-nario-duomenys').select(this.key, {
            'vardas': select('#SN_pareigos xpath:.//h3[1]/br/following-sibling::text()[1]').apply(case_split)[0],
            'pavardė': select('#SN_pareigos xpath:.//h3[1]/br/following-sibling::text()[1]').apply(case_split)[1],
            'mandatas': {
                'nuo': select('#SN_pareigos xpath:.//p/text()[. = " nuo "]/following-sibling::b[1]/text()').replace(' ', '-'),
                'iki': select('#SN_pareigos xpath:.//p/text()[. = " iki "]/following-sibling::b[1]/text()').replace(' ', '-'),
            },
            'išrinktas': func()(' '.join)(join(
                [select('#SN_pareigos xpath:.//p/text()[. = "Išrinktas  "]/following-sibling::b[1]/text()').strip()],
                [select('#SN_pareigos xpath:.//p/text()[. = "Išrinktas  "]/following-sibling::text()[1]').strip()],
            )),
            'iškėlė': select('#SN_pareigos xpath:.//p/text()[. = "iškėlė "]/following-sibling::b[1]?').null().text(),

            'nuotrauka': select('#SN_pareigos img@src'),
            'biografija': select(['xpath://b[text() = "Biografija"]/ancestor::table[1]']).text().replace('\xad', ''),
            'gimė': (
                select(['xpath://b[text() = "Biografija"]/ancestor::table[1]']).text().replace('\xad', '').
                re(r'Gim[eė] (\d{4} \d{2} \d{2})').replace(' ', '-')
            ),
        }),

        # Seimo narių nuotraukos
        task('1990/seimo-nario-duomenys', '1990/seimo-nario-nuotrauka').download(this.value.nuotrauka),

        # 2016 kadencija
        # ==============

        # Seimo narių sąrašas
        task('2016/sąrašo-puslapis').monthly().
        download('http://www.lrs.lt/sip/portal.show?p_r=8801&p_k=1&filtertype=0',
                 cookies=cookies['www.lrs.lt'], check='.smn-list'),

        task('2016/sąrašo-puslapis', '2016/sąrašo-duomenys').select([
            '.smn-list .list-member', (
                'a.smn-name@href', {
                    'vardas': select('a.smn-name:text'),
                    'pavarde': select('a.smn-name > span.smn-pavarde:text'),
                    'nuotrauka': select('.smn-big-photo img@src'),
                },
            ),
        ]),

        # Nuotraukos
        task('2016/sąrašo-duomenys', '2016/seimo-nario-nuotrauka').
        download(this.value.nuotrauka, cookies=cookies['www.lrs.lt']),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
