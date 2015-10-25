#!/usr/bin/env python3

import re
import subprocess
import botlib

from datetime import timedelta
from databot import row, strip, first, value, lower, nspace, call


def clean_company_name(name):
    if name is None:
        return None

    result = []
    strip = re.compile(r'\W+', re.UNICODE)
    words = ' '.join(filter(None, strip.split(name.upper())))

    substitutions = {
        'VIEŠOJI ĮSTAIGA': 'VŠĮ',
        'UŽDAROJI AKCINĖ BENDROVĖ': 'UAB',
        'VIEŠOJI ĮSTAIGA': 'VĮ',
        'INDIVIDUALI ĮMONĖ': 'IĮ',
        'IND. ĮMONĖ': 'IĮ',
        'LIETUVOS RESPUBLIKOS': 'LR',
        'JURBARKO FILIALAS': '',
        'VILNIAUS SKYRIUS': '',
        'LIETUVOS FILIALAS': '',
        'LIETUVOS SKYRIUS': '',
        'FILIALAS LIETUVOJE': '',
        'F KAS': 'FABRIKAS',
    }

    for k, v in substitutions.items():
        words = words.replace(k, v)

    stopwords = {'AB', 'UAB', 'UADB', 'VŠĮ', 'LR', 'VĮ', 'AS', 'ASO'}
    for word in words.split():
        if word not in stopwords:
            result.append(word)
    result = ' '.join(result)

    substitutions = {
        'SEB': 'SEB BANKAS',
        'SEB LIZINGAS': 'SEB BANKAS',
        'SEB GYVYBĖS DRAUDIMAS': 'SEB BANKAS',

        'DNB NORD': 'DNB BANKAS',
        'DND BANKAS': 'DNB BANKAS',
        'DNB NORD': 'DNB BANKAS',
        'BANKAS DNB NORD': 'DNB BANKAS',
        'DNB NORD BANKAS': 'DNB BANKAS',
        'DNB LIZINGAS': 'DNB BANKAS',

        'SWEDBANK': 'SWEDBANK BANKAS',
        'SWEDBANKAS': 'SWEDBANK BANKAS',
        'BANKAS SWEDBANK': 'SWEDBANK BANKAS',
        'SWEDBANK AUTOPARKO VALDYMAS': 'SWEDBANK BANKAS',
        'SWEDBANK LIZINGAS': 'SWEDBANK BANKAS',

        'NORDEA': 'NORDEA BANKAS',
        'NORDEA BANK': 'NORDEA BANKAS',
        'BANKAS NORDEA': 'NORDEA BANKAS',
        'NORDEA BANK FINLAND PLC': 'NORDEA BANKAS',
        'NORDEA FINANCE LITHUANIA': 'NORDEA BANKAS',
        'NORDEA BANK FINLAND PLC': 'NORDEA BANKAS',

        'ŪKIO BANKAS': 'ŪKIO BANKAS',
        'ŪKIO BANKO LIZINGAS': 'ŪKIO BANKAS',

        'ŠIAULIŲ BANKO LIZINGAS': 'ŠIAULIŲ BANKAS',

        'FINASTA LANKSČIOS STRATEGIJOS SUBFONDAS': 'FINASTA',
        'FINASTA RUSIJOS TOP20 SUBFONDAS': 'FINASTA',

        'UNICREDIT LEASING REG NR 302629475': 'UNICREDIT BANKAS',

        'BTA INSURANCE COMPANY SE': 'BTA DRAUDIMAS',

        'LUKOIL BALTIJA': 'LUKOIL',

        'RIBULE': 'RIBULĖ',

        'X': 'NEVIEŠINAMA',
    }

    return substitutions.get(result, result)


def extract(kind, first_key, skip=None):
    skip_default = {(None, None)}
    if skip is not None:
        skip.update(skip_default)
    else:
        skip = skip_default

    def extractor(row):
        for _kind, data in row.value['deklaracijos']:
            if _kind != kind:
                continue

            if _kind == 'KITI DUOMENYS, DĖL KURIŲ GALI KILTI INTERESŲ KONFLIKTAS':
                for key, val in data:
                    yield row.key, {'kita': key}
                continue

            item = {}
            for key, val in data:
                if item and key == first_key:
                    yield row.key, item
                    item = {}
                if (key, val) not in skip:
                    if key in ('Kitos sandorio salies pavadinimas', 'Juridinio asmens pavadinimas'):
                        item['%s (originalus)' % key] = val
                        val = clean_company_name(val)
                    if key == 'Sandorio suma Lt':
                        key = 'Sandorio suma Eur'
                        if val:
                            val = float(val) / 3.45280
                    item[key] = val
            if item:
                yield row.key, item

    return extractor


def select_by_code(data):
    codes = {
        '101',  # Seimo narys
        '102',  # Europos parlamento narys
    }

    for key, val in data:
        if val['code'] in codes:
            # Since downloading is very expencive (we have to wait 7 seconds before each request, we want to download
            # just some declaration pages.
            val['download'] = val['link']
        yield key, val


def define(bot):
    bot.define('sąrašas')
    bot.define('puslapiai')
    bot.define('nuorodos')
    bot.define('deklaracijų puslapiai')
    bot.define('deklaracijos')
    bot.define('seimo nariai')
    bot.define('seimo narių deklaracijų puslapiai')
    bot.define('seimo narių deklaracijos')
    bot.define('sandoriai')
    bot.define('juridiniai')
    bot.define('fiziniai')
    bot.define('individuali veikla')
    bot.define('kita')


def run(bot):
    bot.download_delay = 7  # seconds, vtek.lt denies access if more frequent request are detected

    start_urls = [
        # Seimas (kodas: 188605295)
        'http://www.vtek.lt/paieska/id001/paieska.php?dekl_jkodas=188605295&dekl_vardas=&dekl_pavarde=&rasti=Surasti',
        # Europos parlamentas (kodas: 188648923)
        'http://www.vtek.lt/paieska/id001/paieska.php?dekl_jkodas=188648923&dekl_vardas=&dekl_pavarde=&rasti=Surasti',
    ]

    # Download all pagination pages, redownload after each 7 days
    with bot.pipe('sąrašas').clean(timedelta(days=7)).append(start_urls).dedup():
        with bot.pipe('puslapiai').download():
            with bot.pipe('sąrašas').select(['.panel-body > a@href']).dedup():
                with bot.pipe('puslapiai').download():
                    # We don't want to select page links from each page, they are the same on each page.
                    bot.pipe('sąrašas').skip()

    # Download declaraton pages and group by full name, since URL's are changing
    with bot.pipe('puslapiai'):
        with bot.pipe('seimo nariai').clean(timedelta(days=30)).select(call(select_by_code, [
            'xpath://div[contains(@class,"panel-body") and count(div)=3]', (
                'div[1] > a:text', {               # Person's full name
                    'link': 'div[1] > a@href',     # Link to declaration page
                    'code': strip('div[2]:text'),  # Position code in an institution where this person work
                    'institution': 'div[3]:text',  # Link to declaration page
                }
            )
        ])).dedup():
            bot.pipe('seimo narių deklaracijų puslapiai').download(
                row.value['download'], headers={'Referer': row.value['download']}
            )

    # Extract row data for members of parlament
    with bot.pipe('seimo narių deklaracijų puslapiai'):
        bot.pipe('seimo narių deklaracijos').select(
            nspace(lower('#asmens_duomenys xpath:./tr[contains(td/text(),"DEKLARUOJANTIS ASMUO")]/following-sibling::tr[1]/td/text()')), {  # noqa
                'vtek link': row.key,
                'deklaruojantis asmuo': '#asmens_duomenys xpath:./tr[contains(td/text(),"DEKLARUOJANTIS ASMUO")]/following-sibling::tr[1]/td/text()',  # noqa
                'darbovietė': '#asmens_duomenys xpath:./tr[contains(td/text(),"DARBOVIETĖ")][1]/following-sibling::tr[1]/td/text()',  # noqa
                'pareigos': '#asmens_duomenys xpath:./tr[contains(td/text(),"PAREIGOS")][1]/following-sibling::tr[1]/td/text()',  # noqa
                'sutuoktinis': '#asmens_duomenys xpath:./tr[contains(td/text(),"SUTUOKTINIS, SUGYVENTINIS, PARTNERIS")]/following-sibling::tr[2]/td/text()?',  # noqa
                'sutuoktinio darbovietė': '#asmens_duomenys xpath:./tr[contains(td/text(),"SUTUOKTINIO, SUGYVENTINIO, PARTNERIO DARBOVIETĖ")]/following-sibling::tr[1]/td/text()?',  # noqa
                'sutuoktinio pareigos': '#asmens_duomenys xpath:./tr[contains(td/text(),"PAREIGOS")][2]/following-sibling::tr[1]/td/text()?',  # noqa
                'deklaracijos': [
                    '#pagrindine_priedai #p_virsus', (
                        strip('tr[2] > td:text'), [
                            'xpath:./../../following-sibling::tr[1]/td/table[@id="priedas"]/tr/td/table/tr', (
                                first(strip('td[1]:text'), value(None)),   # Field name
                                first(strip('td[2]:text?'), value(None)),  # Field value
                            )
                        ]
                    )
                ]
            }
        )

    # Extract all kinds of declarations, export them to csv and upload to the server
    extract_args = [
        ('sandoriai', ('SANDORIAI', 'Sandorį sudaręs asmuo', {('Sandoris', None)})),
        ('juridiniai', ('RYŠIAI SU JURIDINIAIS ASMENIMIS', 'Asmuo, kurio ryšys nurodomas')),
        ('fiziniai', ('RYŠIAI SU FIZINIAIS ASMENIMIS', 'Asmuo, kurio ryšys nurodomas')),
        ('individuali veikla', ('INDIVIDUALI VEIKLA', 'Asmuo, kurio individuali veikla toliau bus nurodoma')),
        ('kita', ('KITI DUOMENYS, DĖL KURIŲ GALI KILTI INTERESŲ KONFLIKTAS', None)),
    ]
    for name, args in extract_args:
        csvpath = 'data/%s.csv' % name.replace(' ', '-')
        with bot.pipe('seimo narių deklaracijos'):
            if bot.pipe(name).is_filled():
                bot.pipe(name).clean().reset().call(extract(*args)).export(csvpath)
                subprocess.call(['scp', csvpath, 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data/vtek/seimas'])  # noqa

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
