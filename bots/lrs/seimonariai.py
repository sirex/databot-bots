#!/usr/bin/env python3

import yaml
import botlib

from itertools import groupby
from operator import itemgetter

from databot import define, select, task, this, func, join, oneof, value


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


def date(value, p_asm_id=None):
    spl = value.replace('-', ' ').split()
    if len(spl) == 3:
        return '-'.join(spl)
    elif len(spl) == 4:
        # 1945 balandžio 10 d.
        return '-'.join([spl[0], str(MONTHS[spl[1].lower()]).zfill(2), spl[2].zfill(2)])
    elif len(spl) == 5:
        # 1945 m. balandžio 10 d.
        return '-'.join([spl[0], str(MONTHS[spl[2].lower()]).zfill(2), spl[3].zfill(2)])
    else:
        return value


def replace(value, key=None, table=None):
    if table is None:
        key, table = value, key
    return table.get(key, value)


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

        define('1996/sąrašo-puslapis', compress=True),
        define('1996/sąrašo-duomenys'),
        define('1996/seimo-nario-puslapis', compress=True),
        define('1996/seimo-nario-duomenys'),
        define('1996/seimo-nario-nuotrauka'),

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
        task('1990/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/pls/inter/w5_lrs.seimo_nariu_sarasas?p_kade_id=1',
            cookies=cookies['www3.lrs.lt'],
        ),

        task('1990/sąrašo-puslapis', '1990/sąrašo-duomenys').select([
            'xpath://td[h1/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        # Seimo narių puslapiai
        task('1990/sąrašo-duomenys', '1990/seimo-nario-puslapis').download(
            cookies=cookies['www3.lrs.lt'],
            check='#SN_pareigos',
        ),

        task('1990/seimo-nario-puslapis', '1990/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.urlparse().query.p_asm_id.cast(int),
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
        task('1992/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/pls/inter/w5_lrs.seimo_nariu_sarasas?p_kade_id=2',
            cookies=cookies['www3.lrs.lt'],
        ),

        task('1992/sąrašo-puslapis', '1992/sąrašo-duomenys').select([
            'xpath://td[h1/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        # Seimo narių puslapiai
        task('1992/sąrašo-duomenys', '1992/seimo-nario-puslapis').download(
            this.key.apply(replace, {
                # Pakeisti neveikiančias nuorodas alternatyviomis, kurios veikia.
                'http://www3.lrs.lt/pls/inter/w5_lrs.seimo_narys?p_asm_id=101&p_int_tv_id=0&p_kalb_id=1&p_kade_id=2':
                'http://www3.lrs.lt/docs3/kad2/w5_lrs.seimo_narys-p_asm_id=101&p_int_tv_id=784&p_kalb_id=1&p_kade_id=2.htm',
            }),
            cookies=cookies['www3.lrs.lt'],
            check='#SN_pareigos',
        ),

        task('1992/seimo-nario-puslapis', '1992/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.urlparse().query.p_asm_id.cast(int),
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

            'nuotrauka': select('#SN_pareigos img@src?').apply(replace, this.key.urlparse().query.p_asm_id.cast(int), {
                # Alternatyvios nuotraukos, jei profilyje nepateikta jokia nuotrauka.
                33: 'http://www7.lrs.lt/photo/ImageData5/bb77707f-e589-43a1-a864-7152d9508544.jpg',  # Arūnas EIGIRDAS
                105: 'http://www3.lrs.lt/home/images/VISI/janonis%20j.jpg',  # Juozas JANONIS
            }),
            'biografija': select(['xpath://b[text() = "Biografija"]/ancestor::table[1]']).text().replace('\xad', ''),
            'gimė': (
                select(['xpath://b[text() = "Biografija"]/ancestor::table[1]']).
                text().replace('\xad', '').
                replace('lO', '10').                                       # lO d. -> 10 d.
                sub(r'[O\d]{2,}', lambda m: m.group().replace('O', '0')).  # 3O d. -> 30 d.
                sub(r'[l\d]{2,}', lambda m: m.group().replace('l', '1')).  # l95l m. -> 1951 m.
                sub(r'(\d+)m.', r'\1 m.').                                 # 1935m. -> 1935 m.
                sub(r'(\d+)d.', r'\1 d.').                                 # 15d. -> 15 d.
                re(r'Gim[eė] -? ?(\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.|\d{4} \w+ \d+ d\.)').
                apply(replace, this.key.urlparse().query.p_asm_id.cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    9: '1951-06-13',      # Vytautas ARBAČIAUSKAS
                    16: '1943-02-11',     # Julius BEINORTAS
                    20: '1936-02-01',     # Romualdas Ignas BLOŠKYS
                    21: '1923-03-04',     # Kazys BOBELIS
                    22: '1959-01-02',     # Vytautas BOGUŠIS
                    28: '1939-11-06',     # Virgilijus Vladislovas BULOVAS
                    29: '1954-05-17',     # Sigita BURBIENĖ
                    23809: '1940-07-15',  # Vladas BUTĖNAS
                    32: '1960-05-09',     # Kęstutis DIRGĖLA
                    267: '1930-02-07',    # Vytautas EINORIS
                    35: '1926-02-24',     # Balys GAJAUSKAS
                    49: '1943-03-28',     # Kęstutis GAŠKA
                    39: '1952-12-02',     # Petras GINIOTAS
                    122: '1921-07-27',    # Jonas KUBILIUS
                    123: '1948-01-27',    # Algirdas KUNČINAS
                    125: '1947-03-07',    # Kazimieras KUZMINSKAS
                    133: '1954-04-08',    # Rimantas MARKAUSKAS
                    61: '1940-01-01',     # Kęstutis Povilas PAUKŠTYS
                    69: '1925-12-05',     # Juras POŽELA
                    98: '1959-10-15',     # Virmantas VELIKONIS
                    45: '1950-12-04',     # Vidmantas ŽIEMELIS
                    203: '1942-01-01',    # Justas Vincas PALECKIS
                    46: '1909-01-12',     # Juozas BULAVAS
                    33: '1953-06-11',     # Arūnas EIGIRDAS
                    105: '1962-05-09',    # Juozas JANONIS
                    23: '1932-09-22',     # Algirdas Mykolas BRAZAUSKAS
                }).
                apply(date)
            ),
        }),

        # Seimo narių nuotraukos
        task('1992/seimo-nario-duomenys', '1992/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # VII Seimas (1996–2000)
        # ======================

        # Seimo narių sąrašas
        task('1996/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/seimu_istorija/w3_lrs.seimo_nariu_sarasas-p_kade_id=3&p_kalb_id=1&p_int_tv_id=784.htm',
            cookies=cookies['www3.lrs.lt'],
            check='xpath://td[p/b/h2/text()="Seimo narių sąrašas"]',
        ),

        task('1996/sąrašo-puslapis', '1996/sąrašo-duomenys').select([
            'xpath://td[p/b/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', {
                    'vardas': select(':text').apply(case_split)[0],
                    'pavardė': select(':text').apply(case_split)[1],
                }
            )
        ]),

        # Seimo narių puslapiai
        task('1996/sąrašo-duomenys', '1996/seimo-nario-puslapis').download(
            cookies=cookies['www3.lrs.lt'],
            check='xpath://td[p/b/text() = "Seimo narys "]',
        ),

        task('1996/seimo-nario-puslapis', '1996/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
            'vardas': select('xpath:.//td/p/b/h2/text()').apply(case_split)[0],
            'pavardė': select('xpath://td/p/b/h2/text()').apply(case_split)[1],
            'mandatas': {
                'nuo': select('xpath://td/p/text()[. = " nuo "]/following-sibling::b[1]/text()').replace(' ', '-'),
                'iki': select('xpath://td/p/text()[. = " iki "]/following-sibling::b[1]/text()').replace(' ', '-'),
            },
            'išrinktas': func()(' '.join)(join(
                [select('xpath://td/p/text()[. = "Išrinktas  "]/following-sibling::b[1]/text()').strip()],
                [select('xpath://td/p/text()[. = "Išrinktas  "]/following-sibling::text()[1]').strip()],
            )),
            'iškėlė': select('xpath://td/p/text()[. = "iškėlė "]/following-sibling::b[1]?').null().text(),
            'nuotrauka': (
                select('xpath://img[contains(@tppabs, "seimo_nariu_nuotraukos")]/@src?').
                apply(replace, this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Alternatyvios nuotraukos, jei profilyje nepateikta jokia nuotrauka.
                    7196: 'http://www3.lrs.lt/docs3/kad2/patackas_algirdas.jpg',  # Algirdas Vaclovas PATACKAS
                })
            ),
            'biografija': (
                select(['xpath://p[b/text() = "Biografija"]/following-sibling::div[1]']).
                text().replace('\xad', '')
            ),
            'gimė': (
                select(['xpath://p[b/text() = "Biografija"]/following-sibling::div[1]']).
                text().replace('\xad', '').
                re(r'[Gg]im[eė] (\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.|\d{4} \w+ \d+ d\.)').
                apply(replace, this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    7197: '1935-03-15',      # Feliksas PALUBINSKAS
                    25261: '1953-06-15',     # Dainius Petras PAUKŠTĖ
                    23939: '1961-02-02',     # Virginijus ŠMIGELSKAS
                    7247: '1935-03-26',      # Zigmantas POCIUS
                    7219: '1937-10-27',      # Raimundas Leonas RAJECKAS
                    7243: '1926-11-16',      # Romualdas SIKORSKIS
                }).
                apply(date)
            ),
            'narystė': [
                'xpath://p[b/text() = "Biografija"]/preceding-sibling::ul[1]/li', oneof(
                    {
                        'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                        'url': select('a@href'),
                        'padalinys': select('a:text'),
                        'pareigos': select('xpath:text()[1]').splitlines()[0],
                        'nuo': (
                            select('xpath:text()[1]').
                            splitlines()[1].
                            replace('\xad', '').
                            re(r'\d{4} \d{2} \d{2}').
                            apply(date)
                        ),
                        'iki': (
                            select('xpath:b/text()').
                            replace('\xad', '').
                            re(r'\d{4} \d{2} \d{2}').
                            apply(date)
                        ),
                    },
                    {
                        'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                        'url': value(None),
                        'padalinys': select('xpath:.').text().rsplit('(', 1)[0].rsplit(',', 1)[0],
                        'pareigos': select('xpath:.').text().rsplit('(', 1)[0].rsplit(',', 1)[1],
                        'nuo': select('xpath:.').text().re(r'nuo (\d{4} \d{2} \d{2})').apply(date),
                        'iki': select('xpath:.').text().re(r'iki (\d{4} \d{2} \d{2})').apply(date),
                    },
                    {
                        'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                        'url': value(None),
                        'padalinys': select('xpath:.').text().rsplit(',', 1)[0],
                        'pareigos': select('xpath:.').text().rsplit(',', 1)[1],
                        'nuo': value(None),
                        'iki': value(None),
                    },
                    {
                        'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                        'url': value(None),
                        'padalinys': select('xpath:.').text(),
                        'pareigos': value(None),
                        'nuo': value(None),
                        'iki': value(None),
                    },
                ),
            ],
        }),

        # Seimo narių nuotraukos
        task('1996/seimo-nario-duomenys', '1996/seimo-nario-nuotrauka').download(this.value.nuotrauka),


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
