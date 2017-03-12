#!/usr/bin/env python3

import yaml
import botlib

from itertools import groupby
from operator import itemgetter

from databot import define, select, task, this, func, join


MONTHS = {
    'sausio': 1,
    'vasario': 2,
    'kovo': 3,
    'balandžio': 4,
    'gegužės': 5,
    'birželio': 6,
    'liepos': 7,
    'rugpjūčio': 8,
    'rugsėjo': 9,
    'spalio': 10,
    'lapkričio': 11,
    'gruodžio': 12,
}


def date(value):
    spl = value.split()
    if len(spl) == 3:
        return '-'.join(spl)
    elif len(spl) == 5:
        # 1945 m. balandžio 10 d.
        return '-'.join([spl[0], str(MONTHS[spl[2].lower()]).zfill(2), spl[3].zfill(2)])
    else:
        return value


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

        define('1992/sąrašo-puslapis', compress=True),
        define('1992/sąrašo-duomenys'),
        define('1992/seimo-nario-puslapis', compress=True),
        define('1992/seimo-nario-duomenys'),
        define('1992/seimo-nario-nuotrauka'),

        define('2016/sąrašo-puslapis', compress=True),
        define('2016/sąrašo-duomenys'),
        define('2016/seimo-nario-nuotrauka'),
    ],
    'tasks': [
        # Seimų istorija:
        # http://www.lrs.lt/sip/portal.show?p_r=16308&p_k=1


        # V Seimas – Aukščiausioji Taryba – Atkuriamasis Seimas (1990–1992)
        # =================================================================

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
                re(r'Gim[eė] (\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.)').apply(date)
            ),
        }),

        # Seimo narių nuotraukos
        task('1990/seimo-nario-duomenys', '1990/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # VI Seimas (1992–1996)
        # =====================

        # Seimo narių sąrašas
        task('1992/sąrašo-puslapis').monthly().
        download('http://www3.lrs.lt/pls/inter/w5_lrs.seimo_nariu_sarasas?p_kade_id=2',
                 cookies=cookies['www3.lrs.lt']),

        task('1992/sąrašo-puslapis', '1992/sąrašo-duomenys').select([
            'xpath://td[h1/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        # Seimo narių puslapiai
        task('1992/sąrašo-duomenys', '1992/seimo-nario-puslapis').
        update({
            # Seimo narių sąrše nuoroda rodo į neegzistuojantį puslapį, tačiau yra kopija kitoje vietoje.
            'http://www3.lrs.lt/pls/inter/w5_lrs.seimo_narys?p_asm_id=101&p_int_tv_id=0&p_kalb_id=1&p_kade_id=2': {
                'url': 'http://www3.lrs.lt/docs3/kad2/w5_lrs.seimo_narys-p_asm_id=101&p_int_tv_id=784&p_kalb_id=1&p_kade_id=2.htm',
            }
        }).
        download(cookies=cookies['www3.lrs.lt'], check='#SN_pareigos'),

        task('1992/seimo-nario-puslapis', '1992/seimo-nario-duomenys').select(this.key, {
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
                select(['xpath://b[text() = "Biografija"]/ancestor::table[1]']).
                text().replace('\xad', '').
                replace('O', '0').                                         # 3O d. -> 30 d.
                sub(r'[l\d]{2,}', lambda m: m.group().replace('l', '1')).  # l95l m. -> 1951 m.
                sub(r'(\d+)m.', r'\1 m.').                                 # 1935m. -> 1935 m.
                re(r'Gim[eė] -? ?(\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.)').
                apply(date)
            ),
        }),

        # Seimo narių nuotraukos
        task('1992/seimo-nario-duomenys', '1992/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # # 2016 kadencija
        # # ==============

        # # Seimo narių sąrašas
        # task('2016/sąrašo-puslapis').monthly().
        # download('http://www.lrs.lt/sip/portal.show?p_r=8801&p_k=1&filtertype=0',
        #          cookies=cookies['www.lrs.lt'], check='.smn-list'),

        # task('2016/sąrašo-puslapis', '2016/sąrašo-duomenys').select([
        #     '.smn-list .list-member', (
        #         'a.smn-name@href', {
        #             'vardas': select('a.smn-name:text'),
        #             'pavarde': select('a.smn-name > span.smn-pavarde:text'),
        #             'nuotrauka': select('.smn-big-photo img@src'),
        #         },
        #     ),
        # ]),

        # # Nuotraukos
        # task('2016/sąrašo-duomenys', '2016/seimo-nario-nuotrauka').
        # download(this.value.nuotrauka, cookies=cookies['www.lrs.lt']),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
