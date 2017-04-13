#!/usr/bin/env python3

import yaml
import botlib

from itertools import groupby, zip_longest
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
    elif len(spl) == 6:
        # 1945 m. balandžio mėn 10 d.
        return '-'.join([spl[0], str(MONTHS[spl[2].lower()]).zfill(2), spl[4].zfill(2)])
    else:
        return value


def replace(value, key=None, table=None):
    if table is None:
        key, table = value, key
    return table.get(key, value)


def case_split(value):
    words = [(w.isupper(), w) for w in value.split()]
    return [' '.join([x for _, x in g]) for k, g in groupby(words, key=itemgetter(0))]


def bio(value):
    result = []
    for key, value in value:
        for k, v in zip_longest(key, value):
            result.append((k, v))
    return result


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

        define('2000/sąrašo-puslapis', compress=True),
        define('2000/sąrašo-duomenys'),
        define('2000/seimo-nario-puslapis', compress=True),
        define('2000/seimo-nario-duomenys'),
        define('2000/seimo-nario-nuotrauka'),

        define('2004/sąrašo-puslapis', compress=True),
        define('2004/sąrašo-duomenys'),
        define('2004/seimo-nario-puslapis', compress=True),
        define('2004/seimo-nario-duomenys'),
        define('2004/seimo-nario-nuotrauka'),

        define('2008/sąrašo-puslapis', compress=True),
        define('2008/sąrašo-duomenys'),
        define('2008/seimo-nario-puslapis', compress=True),
        define('2008/seimo-nario-duomenys'),
        define('2008/seimo-nario-nuotrauka'),

        define('2012/sąrašo-puslapis', compress=True),
        define('2012/sąrašo-duomenys'),
        define('2012/seimo-nario-puslapis/meniu'),
        define('2012/seimo-nario-puslapis/pareigos', compress=True),
        define('2012/seimo-nario-puslapis/veikla', compress=True),
        define('2012/seimo-nario-puslapis/biografija', compress=True),
        define('2012/seimo-nario-duomenys'),
        define('2012/seimo-nario-nuotrauka'),

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
            this.key.bypass({
                # Pakeisti neveikiančias nuorodas alternatyviomis, kurios veikia.
                'http://www3.lrs.lt/pls/inter/w5_lrs.seimo_narys?p_asm_id=101&p_int_tv_id=0&p_kalb_id=1&p_kade_id=2':
                'http://www3.lrs.lt/docs3/kad2/w5_lrs.seimo_narys-p_asm_id=101&p_int_tv_id=784&p_kalb_id=1&p_kade_id=2.htm',
            }),
            cookies=cookies['www3.lrs.lt'],
            check='#SN_pareigos',
        ),

        task('1992/seimo-nario-puslapis', '1992/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
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

            'nuotrauka': (
                select('#SN_pareigos img@src?').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Alternatyvios nuotraukos, jei profilyje nepateikta jokia nuotrauka.
                    33: 'http://www7.lrs.lt/photo/ImageData5/bb77707f-e589-43a1-a864-7152d9508544.jpg',  # Arūnas EIGIRDAS
                    105: 'http://www3.lrs.lt/home/images/VISI/janonis%20j.jpg',  # Juozas JANONIS
                }).
                notnull()
            ),
            'biografija': (
                select('xpath://b[text() = "Biografija"]/ancestor::table[1]?').
                null().text().replace('\xad', '')
            ),
            'gimė': (
                select('xpath://b[text() = "Biografija"]/ancestor::table[1]?').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
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
                    101: '1941-10-25',    # Romualda HOFERTIENĖ
                    108: '1945-07-07',    # Leonardas Kęstutis JASKELEVIČIUS
                }).
                text().replace('\xad', '').
                replace('lO', '10').                                       # lO d. -> 10 d.
                sub(r'[O\d]{2,}', lambda m: m.group().replace('O', '0')).  # 3O d. -> 30 d.
                sub(r'[l\d]{2,}', lambda m: m.group().replace('l', '1')).  # l95l m. -> 1951 m.
                sub(r'(\d+)m.', r'\1 m.').                                 # 1935m. -> 1935 m.
                sub(r'(\d+)d.', r'\1 d.').                                 # 15d. -> 15 d.
                re(r'Gim[eė] -? ?(\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.|\d{4} \w+ \d+ d\.)').
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
            this.key.bypass({
                # Pakeisti neveikiančias nuorodas alternatyviomis, kurios veikia.
                'http://www3.lrs.lt/seimu_istorija/w3_lrs.seimo_narys-p_asm_id=7200&p_int_tv_id=784&p_kalb_id=1&p_kade_id=3.htm':
                'http://www3.lrs.lt/seimu_istorija/w3_lrs.seimo_narys-p_asm_id=47830&p_int_tv_id=784&p_kalb_id=1&p_kade_id=3.htm',
            }),
            cookies=cookies['www3.lrs.lt'],
            check=oneof(
                select('xpath://td[p/b/text() = "Seimo narys "]'),
                select('xpath://td[p/b/text() = "Seimo narė "]'),
            ),
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
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Alternatyvios nuotraukos, jei profilyje nepateikta jokia nuotrauka.
                    7196: 'http://www3.lrs.lt/docs3/kad2/patackas_algirdas.jpg',  # Algirdas Vaclovas PATACKAS
                }).
                notnull()
            ),
            'biografija': (
                select(['xpath://p[b/text() = "Biografija"]/following-sibling::div[1]']).
                text().replace('\xad', '')
            ),
            'gimė': (
                select('xpath://p[b/text() = "Biografija"]/following-sibling::div[1]').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    7197: '1935-03-15',      # Feliksas PALUBINSKAS
                    25261: '1953-06-15',     # Dainius Petras PAUKŠTĖ
                    23939: '1961-02-02',     # Virginijus ŠMIGELSKAS
                    7247: '1935-03-26',      # Zigmantas POCIUS
                    7219: '1937-10-27',      # Raimundas Leonas RAJECKAS
                    7243: '1926-11-16',      # Romualdas SIKORSKIS
                    7407: '1952-04-16',      # Danutė ALEKSIŪNIENĖ
                    178: '1958-01-26',       # Rasa JUKNEVIČIENĖ
                }).
                text().replace('\xad', '').
                re(r'[Gg]im[eė] (\d{4} \d{2} \d{2}|\d{4} m\. \w+ \d+ d\.|\d{4} \w+ \d+ d\.)').
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


        # VIII Seimas (2000-2004)
        # =======================

        # Seimo narių sąrašas
        task('2000/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/docs3/kad4/w3_lrs.seimo_nariu_sarasas-p_kade_id=4&p_kalb_id=1&p_int_tv_id=784.htm',
            cookies=cookies['www3.lrs.lt'],
            check='xpath://td[p/b/h2/text()="Seimo narių sąrašas"]',
        ),

        task('2000/sąrašo-puslapis', '2000/sąrašo-duomenys').select([
            'xpath://td[p/b/h2/text()="Seimo narių sąrašas"]/ol/li/a', (
                '@href', oneof(
                    {
                        'vardas': select(':text').apply(case_split)[0],
                        'pavardė': select(':text').apply(case_split)[1],
                    },
                    {
                        'vardas': select('b:text').apply(case_split)[0],
                        'pavardė': select('b:text').apply(case_split)[1],
                    },
                ),
            )
        ]),

        # Seimo narių puslapiai
        task('2000/sąrašo-duomenys', '2000/seimo-nario-puslapis').download(
            cookies=cookies['www3.lrs.lt'],
            check=oneof(
                'xpath://td[p/b/text() = "Seimo narys "]',
                'xpath://td[p/b/text() = "Seimo narė "]',
            ),
        ),

        task('2000/seimo-nario-puslapis', '2000/seimo-nario-duomenys').select(this.key, {
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
            'nuotrauka': select('xpath://img[contains(@tppabs, "seimo_nariu_nuotraukos")]/@src'),
            'biografija': (
                select('xpath://p[b/text() = "Biografija"]/following-sibling::div[1]?').null().
                text().replace('\xad', '')
            ),
            'gimė': (
                select('xpath://p[b/text() = "Biografija"]/following-sibling::div[1]?').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    7229: '1957-05-04',      # Vilija ALEKNAITĖ ABRAMIKIENĖ
                    26227: '1940-12-17',     # Dobilas Jonas KIRVELIS
                    47217: '1956-04-13',     # Alfonsas MACAITIS
                    23841: '1960-12-08',     # Saulius NEFAS
                    47248: '1963-06-11',     # Ilona STULPINIENĖ
                    47794: '1964-07-29',     # Gražina ŠMIGELSKIENĖ
                    23785: '1952-05-16',     # Antanas VALYS
                    37132: '1930-11-26',     # Vytautas ZABIELA
                    47811: '1957-03-23',     # Kęstutis MASIULIS
                    111: '1944-02-16',     # Vytautas JUŠKUS
                    7208: '1958-01-17',     # Audronius AŽUBALIS
                }).
                text().replace('\xad', '').
                re(r'[Gg]im[eė] (%s)' % '|'.join([
                    r'\d{4} \d{2} \d{2}',
                    r'\d{4} m\. \w+ \d+ d\.',
                    r'\d{4} m\. \w+ mėn\. \d+ d\.',
                    r'\d{4} m\. \w+ \d+ dieną',
                    r'\d{4} \w+ \d+ d\.',
                ])).
                apply(date)
            ),
            'narystė': [
                'xpath://p[b/text() = "Biografija"]/preceding-sibling::ul[1]/li?', oneof(
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
        task('2000/seimo-nario-duomenys', '2000/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # IX Seimas (2004-2008)
        # =====================

        # Seimo narių sąrašas
        task('2004/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/docs3/kad5/w5_istorija.show5-p_r=786&p_k=1.html',
            cookies=cookies['www3.lrs.lt'],
            check='xpath://div/center/h2[text() = "2004 – 2008 m. SEIMO KADENCIJA"]',
        ),

        task('2004/sąrašo-puslapis', '2004/sąrašo-duomenys').select([
            '.turinys xpath:.//table/tr[contains(td//text(), "Vardas,")]/following-sibling::tr', (
                'xpath:td[2]/a/@href', {
                    'vardas': select('xpath:td[2]/a/text()[1]'),
                    'pavardė': select('xpath:td[2]/a/strong/text()'),
                },
            ),
        ]),

        # Seimo narių puslapiai
        task('2004/sąrašo-duomenys', '2004/seimo-nario-puslapis').download(
            cookies=cookies['www3.lrs.lt'],
            check=oneof(
                '#smain xpath:.//td[b/text() = "Seimo narys "]',
                '#smain xpath:.//td[b/text() = "Seimo narė "]',
            ),
        ),

        task('2004/seimo-nario-puslapis', '2004/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
            'vardas': select('#smain xpath:./table[1]//h3/text()').apply(case_split)[0],
            'pavardė': select('#smain xpath:./table[1]//h3/text()').apply(case_split)[1],
            'mandatas': {
                'nuo': select('#smain xpath:.//td/text()[. = " nuo "]/following-sibling::b[1]/text()'),
                'iki': select('#smain xpath:.//td/text()[. = " iki "]/following-sibling::b[1]/text()'),
            },
            'išrinktas': oneof(
                func()(' '.join)(join(
                    [select('#smain xpath://td/text()[. = "Išrinktas  "]/following-sibling::b[1]/text()').strip()],
                    [select('#smain xpath://td/text()[. = "Išrinktas  "]/following-sibling::text()[1]').strip()],
                )),
                func()(' '.join)(join(
                    [select('#smain xpath://td/text()[. = "Išrinkta  "]/following-sibling::b[1]/text()').strip()],
                    [select('#smain xpath://td/text()[. = "Išrinkta  "]/following-sibling::text()[1]').strip()],
                )),
            ),
            'iškėlė': select('#smain xpath://td/text()[. = "iškėlė "]/following-sibling::b[1]?').null().text(),
            'nuotrauka': select('#smain xpath:table[1]/tr/td/div/img/@src'),
            'biografija': (
                select('#smain xpath:div[text() = "Biografija"]/following-sibling::div[1]?').null().
                text().replace('\xad', '')
            ),
            'gimė': (
                select('#smain xpath:div[text() = "Biografija"]/following-sibling::div[1]?').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    18: '1935-09-08',        # Juozas BERNATONIS
                    47856: '1967-10-10',     # Saulius BUCEVIČIUS
                    47844: '1960-01-31',     # Kęstutis DAUKŠYS
                    23547: '1953-11-18',     # Valentinas MAZURONIS
                    47846: '1960-03-22',     # Gintautas BUŽINSKAS
                    7444: '1946-01-08',      # Kęstutis ČILINSKAS
                    48529: '1941-10-17',     # Algirdas GAIŽUTIS
                    47855: '1966-06-09',     # Aidas GEDVILAS
                    48519: '1960-11-05',     # Bronius MARKAUSKAS
                    47851: '1962-12-04',     # Žilvinas PADAIGA
                    39605: '1944-07-03',     # Rolandas PAVILIONIS
                    47831: '1949-04-10',     # Vladimiras PRUDNIKOVAS
                    47226: '1955-03-31',     # Alvydas RAMANAUSKAS
                    23279: '1955-04-14',     # Bronis ROPĖ
                    23760: '1951-01-23',     # Kazys SIVICKIS
                    48197: '1969-04-04',     # Rytis ŠATKAUSKAS
                    48533: '1958-04-09',     # Gema UMBRASIENĖ
                    47204: '1959-07-24',     # Viktor USPASKICH
                    47857: '1959-07-24',     # Artūras ZUOKAS
                }).
                text().replace('\xad', '').
                re(r'[Gg]im[eė] (%s)' % '|'.join([
                    r'\d{4} \d{2} \d{2}',
                    r'\d{4} m\. \w+ \d+ d\.',
                    r'\d{4} m\. \w+ mėn\. \d+ d\.',
                    r'\d{4} m\. \w+ \d+ dieną',
                    r'\d{4} \w+ \d+ d\.',
                ])).
                apply(date)
            ),
            'frakcijos': ['#smain xpath:b[text() = "Seimo frakcijose"]/following-sibling::ul[1]/li', {
                'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                'p_pad_id': select('a@href').re(r'p_pad_id=([\d-]+)').cast(int),
                'frakcija': select('a:text'),
                'url': select('a@href'),
                'pareigos': select('xpath:.').text().rsplit(',', 1)[1],
                'nuo': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[0].apply(date),
                'iki': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[1].apply(date),
            }],
            'narystė': [
                '#smain xpath:b[%s]/following-sibling::ul[1]/li' % ' or '.join([
                    'text() = "%s"' % x for x in [
                        'Seimo komitetuose',
                        'Seimo komisijose',
                        'Paralamentinėse grupėse',
                    ]
                ]),
                {
                    'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                    'url': select('a@href'),
                    'tipas': select('xpath:../preceding-sibling::b[1]/text()'),
                    'padalinys': select('a:text'),
                    'pareigos': select('xpath:.').text().rsplit(',', 1)[1].split('(', 1)[0],
                    'nuo': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[0].apply(date),
                    'iki': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[1].apply(date),
                },
            ],
        }),

        # Seimo narių nuotraukos
        task('2004/seimo-nario-duomenys', '2004/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # X Seimas (2008-2012)
        # ====================

        # Seimo narių sąrašas
        task('2008/sąrašo-puslapis').monthly().download(
            'http://www3.lrs.lt/docs3/kad6/w6_istorija.show6-p_r=6113&p_k=1.html',
            cookies=cookies['www3.lrs.lt'],
            check='xpath://div/center/h2[text() = "2008 – 2012 m. SEIMO KADENCIJA"]',
        ),

        task('2008/sąrašo-puslapis', '2008/sąrašo-duomenys').select([
            '#divDesContent xpath:.//table/tr[contains(td//text(), "Vardas,")]/following-sibling::tr', (
                'xpath:td[2]/a/@href', {
                    'vardas': select('xpath:td[2]/a/text()[1]'),
                    'pavardė': select('xpath:td[2]/a/strong/text()'),
                },
            ),
        ]),

        # Seimo narių puslapiai
        task('2008/sąrašo-duomenys', '2008/seimo-nario-puslapis').download(
            cookies=cookies['www3.lrs.lt'],
            check=oneof(
                '#divDesContent xpath:.//td[b/text() = "Seimo narys "]',
                '#divDesContent xpath:.//td[b/text() = "Seimo narė "]',
            ),
        ),

        task('2008/seimo-nario-puslapis', '2008/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
            'vardas': select('xpath://table[@summary = "Kadencijos"]/tr[1]/td[2]/div/b/font/text()').apply(case_split)[0],
            'pavardė': select('xpath://table[@summary = "Kadencijos"]/tr[1]/td[2]/div/b/font/text()').apply(case_split)[1],
            'mandatas': {
                'nuo': select('#divDesContent xpath:.//td/text()[. = " nuo "]/following-sibling::b[1]/text()'),
                'iki': select('#divDesContent xpath:.//td/text()[. = " iki "]/following-sibling::b[1]/text()'),
            },
            'išrinktas': oneof(
                func()(' '.join)(join(
                    [select('#divDesContent xpath://td/text()[. = "Išrinktas  "]/following-sibling::b[1]/text()').strip()],
                    [select('#divDesContent xpath://td/text()[. = "Išrinktas  "]/following-sibling::text()[1]').strip()],
                )),
                func()(' '.join)(join(
                    [select('#divDesContent xpath://td/text()[. = "Išrinkta  "]/following-sibling::b[1]/text()').strip()],
                    [select('#divDesContent xpath://td/text()[. = "Išrinkta  "]/following-sibling::text()[1]').strip()],
                )),
            ),
            'iškėlė': select('#divDesContent xpath://td/text()[. = "iškėlė "]/following-sibling::b[1]?').null().text(),
            'nuotrauka': select('xpath://table[@summary = "seimo nario foto, pagrindinė info"]/tr/td/div/img/@src'),
            'biografija': (
                select('#divDesContent xpath:.//div[text() = "Biografija"]/following-sibling::div[1]?').null().
                text().replace('\xad', '')
            ),
            'gimė': (
                select('#divDesContent xpath:.//div[text() = "Biografija"]/following-sibling::div[1]?').
                bypass(this.key.re(r'p_asm_id=([\d-]+)').cast(int), {
                    # Pataisyti trūkstamas arba neįprastai užrašytas gimimo datas biografijos tekste.
                    7404: '1959-04-16',        # Raimundas ALEKNA
                    47220: '1953-11-16',       # Zigmantas BALČYTIS
                    7326: '1960-03-03',        # Vilija BLINKEVIČIŪTĖ
                    47898: '1978-04-15',       # Andrius BURBA
                    47769: '1941-01-08',       # Juozas IMBRASAS
                    43989: '1943-08-15',       # Jonas KONDROTAS
                    47905: '1970-09-11',       # Evaldas LEMENTAUSKAS
                    39007: '1953-03-27',       # Albinas MITRULEVIČIUS
                    53928: '1966-01-09',       # Daiva TAMOŠIŪNAITĖ
                    23705: '1965-03-03',       # Valdemar TOMAŠEVSKI
                    47204: '1959-07-24',       # Viktor USPASKICH
                }).
                text().replace('\xad', '').
                re(r'[Gg]im[eė] (%s)' % '|'.join([
                    r'\d{4}-\d{2}-\d{2}',
                    r'\d{4} \d{2} \d{2}',
                    r'\d{4} m\. \w+ \d+ d\.',
                    r'\d{4} m\. \w+ mėn\. \d+ d\.',
                    r'\d{4} m\. \w+ \d+ dieną',
                    r'\d{4} \w+ \d+ d\.',
                ])).
                apply(date)
            ),
            'frakcijos': ['#divDesContent xpath:.//td/b[text() = "Seimo frakcijose"]/following-sibling::ul[1]/li', {
                'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                'p_pad_id': select('a@href').re(r'p_pad_id=([\d-]+)').cast(int),
                'frakcija': select('a:text'),
                'url': select('a@href'),
                'pareigos': select('xpath:.').text().rsplit(',', 1)[1],
                'nuo': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[0].apply(date),
                'iki': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[1].apply(date),
            }],
            'narystė': [
                '#divDesContent xpath:.//td/b[%s]/following-sibling::ul[1]/li' % ' or '.join([
                    'text() = "%s"' % x for x in [
                        'Seimo komitetuose',
                        'Seimo komisijose',
                        'Paralamentinėse grupėse',
                    ]
                ]),
                {
                    'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                    'url': select('a@href'),
                    'tipas': select('xpath:../preceding-sibling::b[1]/text()'),
                    'padalinys': select('a:text'),
                    'pareigos': select('xpath:.').text().rsplit(',', 1)[1].split('(', 1)[0],
                    'nuo': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[0].apply(date),
                    'iki': select('xpath:.').text().rall(r'\d{4}-\d{2}-\d{2}')[1].apply(date),
                },
            ],
        }),

        # Seimo narių nuotraukos
        task('2008/seimo-nario-duomenys', '2008/seimo-nario-nuotrauka').download(this.value.nuotrauka),


        # XI Seimas (2012-2016)
        # =====================

        # Seimo narių sąrašas
        task('2012/sąrašo-puslapis').monthly().download(
            'http://www.lrs.lt/sip/portal.show?p_r=15828&p_k=1',
            cookies=cookies['www.lrs.lt'],
            check='.smn-list .smn-name',
        ),

        task('2012/sąrašo-puslapis', '2012/sąrašo-duomenys').select([
            '.smn-list .list-member', (
                'a.smn-name@href', {
                    'vardas': select('a.smn-name:text'),
                    'pavardė': select('a.smn-name .smn-pavarde:text'),
                },
            ),
        ]),

        # Seimo narių puslapiai
        task('2012/sąrašo-duomenys', '2012/seimo-nario-puslapis/pareigos').download(
            cookies=cookies['www.lrs.lt'],
            check='.smn-page',
            update={
                'vardas': this.value.vardas,
                'pavarde': this.value.pavarde,
            },
        ),

        task('2012/seimo-nario-puslapis/pareigos', '2012/seimo-nario-puslapis/meniu').select(this.key, {
            'veikla': select('.tabs-tbl xpath:.//a[text() = "Veikla"]/@href'),
            'biografija': select('.tabs-tbl xpath:.//a[text() = "Biografija"]/@href'),
        }),

        task('2012/seimo-nario-puslapis/meniu', '2012/seimo-nario-puslapis/veikla').download(
            this.value.veikla,
            cookies=cookies['www.lrs.lt'],
            check='.smn-page',
            update={
                'source': this.key,
            },
        ),

        task('2012/seimo-nario-puslapis/meniu', '2012/seimo-nario-puslapis/biografija').download(
            this.value.biografija,
            cookies=cookies['www.lrs.lt'],
            check='.smn-page',
            update={
                'source': this.key,
            },
        ),


        task('2012/seimo-nario-puslapis/pareigos', '2012/seimo-nario-duomenys').select(this.key, {
            'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
            'vardas': this.value.vardas,
            'pavardė': this.value.pavarde,
            'mandatas': {
                'nuo': select('.smn-nuo-iki xpath:b[1]/text()'),
                'iki': select('.smn-date-iki xpath:b[1]/text()'),
            },
            'išrinktas': oneof(
                select('.smn-page xpath:.//p[text() = "Išrinktas:"]/b/text()'),
                select('.smn-page xpath:.//p[text() = "Išrinkta:"]/b/text()'),
            ),
            'iškėlė': select('.smn-page xpath:.//p[text() = "Iškėlė:"]/b/text()'),
            'nuotrauka': select('.smn-page .foto img@src'),
            'frakcijos': select([
                'xpath://h3[contains(@class, "smn-veikl-grup-pavad") and text() = "Seimo frakcijose"]/following-sibling::table[1]/tr', {
                    'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                    'p_pad_id': select('a@href').re(r'p_pad_id=([\d-]+)').cast(int),
                    'frakcija': select('a:text'),
                    'url': select('a@href'),
                    'pareigos': select('a').text().rsplit(',', 1)[1].strip(),
                    'nuo': select('td.smn-par-data:text').split(' – ')[0],
                    'iki': select('td.smn-par-data:text').split(' – ')[1],
                },
            ]),
            'narystė': [
                'xpath://h3[contains(@class, "smn-veikl-grup-pavad") and (%s)]/following-sibling::table[1]/tr' % ' or '.join([
                    'text() = "%s"' % x for x in [
                        'Seimo komitetuose',
                        'Seimo komisijose',
                        'Paralamentinėse grupėse',
                    ]
                ]),
                {
                    'p_asm_id': this.key.re(r'p_asm_id=([\d-]+)').cast(int),
                    'p_pad_id': select('a@href').re(r'p_pad_id=([\d-]+)').cast(int),
                    'tipas': select('xpath:../preceding-sibling::h3[1]/text()'),
                    'pavadinimas': select('a:text'),
                    'url': select('a@href'),
                    'pareigos': select('a').text().rsplit(',', 1)[1].strip(),
                    'nuo': select('td.smn-par-data:text').split(' – ')[0],
                    'iki': select('td.smn-par-data:text').split(' – ')[1],
                },
            ],
        }),

        task('2012/seimo-nario-puslapis/biografija', '2012/seimo-nario-duomenys').select(this.value.source, {
            'biografija': select([
                '.smn-page .pl-head-container > table.MsoNormalTable tr', (
                    [select('td[1] > p').text().replace('\xad', '')],
                    [select('td[2] > p').text().replace('\xad', '')],
                ),
            ]).apply(bio),
            'gimė': select([
                '.smn-page .pl-head-container > table.MsoNormalTable tr', (
                    [select('td[1] > p').text().replace('\xad', '')],
                    [select('td[2] > p').text().replace('\xad', '')],
                ),
            ]).apply(bio).apply(dict)['Gimimo data'].apply(date),
        }),

        # Seimo narių nuotraukos
        task('2012/seimo-nario-duomenys', '2012/seimo-nario-nuotrauka').download(
            this.value.nuotrauka,
            cookies=cookies['www.lrs.lt'],
        ),



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
