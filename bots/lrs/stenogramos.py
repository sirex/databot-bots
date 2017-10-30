#!/usr/bin/env python3

import os
import sys
import botlib
import yaml
import re
import datetime
import lxml.etree
import pandas as pd

from itertools import tee
from pprintpp import pprint
from subprocess import run, PIPE
from tempfile import NamedTemporaryFile

from databot import Bot, define, select, task, this, func


def attachment(value):
    """Select prefered attachment format."""
    formats = [x.split('/')[-2] for x in value]
    for x in ('MSO2010_DOCX', 'MSO2003_DOC'):
        if x in formats:
            return value[formats.index(x)]
    return value[0] if value else None


def xtodocbook(content, mime):
    if mime == 'application/msword':
        return run(['antiword', '-x', 'db', '-'], input=content, stdout=PIPE, check=True).stdout.decode('utf-8')
    elif mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        with NamedTemporaryFile(prefix='databot_', suffix='.docx', delete=False) as f:
            f.write(content)
            f.close()
            try:
                return (
                    run(['pandoc', '-s', '-f', 'docx', '-t', 'docbook', f.name], stdout=PIPE, check=True).
                    stdout.decode('utf-8').replace('\xad', '').replace('\xa0', ' ')
                )
            finally:
                os.remove(f.name)
    else:
        raise RuntimeError("Unknown mime type: %r." % mime)


def find_chairman(date):
    global CHAIRMANS
    result = CHAIRMANS[(CHAIRMANS.start < date) & ((CHAIRMANS.end > date) | (CHAIRMANS.end.isnull()))]
    if len(result):
        result = result.iloc[0].to_dict()
        result['start'] = result['start'].strftime('%Y-%m-%d')
        result['end'] = result['end'].strftime('%Y-%m-%d') if result['end'] is not pd.NaT else None
        return result


def find_mp(speaker, date):
    global SEIMONARIAI
    surname = extract_surname(speaker)
    query = (
        (SEIMONARIAI['nuo'] < date) &
        ((SEIMONARIAI['iki'] > date) | (SEIMONARIAI['iki'].isnull())) &
        (SEIMONARIAI['pavardė'].str.upper() == surname.upper())
    )
    result = SEIMONARIAI[query]
    speaker = re.sub(r'[.\s]+', ' ', speaker).upper().strip()
    for index, row in result.iterrows():
        letters = [x[0] for x in row.vardas.split()]
        names = [
            ' '.join(letters + [row.pavardė]).upper(),
            ' '.join(letters[:1] + [row.pavardė]).upper(),
            ' '.join(letters[:-1] + [row.pavardė]).upper(),
            ' '.join(list(reversed(letters)) + [row.pavardė]).upper(),
            row.pavardė.upper(),
        ]
        for name in names:
            if speaker == name:
                mp = row.to_dict()
                mp['nuo'] = mp['nuo'].strftime('%Y-%m-%d')
                mp['iki'] = mp['iki'].strftime('%Y-%m-%d') if mp['iki'] is not pd.NaT else None
                return mp


def is_parliamentary_group(s):
    if ' ' in s or '.' in s:
        return False
    for a, b in zip(s, s[1:]):
        if a.isupper() and b.isupper():
            return True
    return False


def extract_text(xml):
    # Recursively extract all texts
    def extract(nodes, tail=False):
        texts = []
        for node in nodes:
            if isinstance(node, str):
                texts.append(node)
                continue
            if node.tag is lxml.etree.Comment:
                continue
            if node.tag in ('articleinfo', 'footnote'):
                if tail and node.tail:
                    texts.append(node.tail)
                continue

            texts.append(node.text)
            texts.extend(extract(node.getchildren(), tail=True))
            if node.tag in ('para', 'br', 'literallayout'):
                texts.append('\n')
            if tail and node.tail:
                texts.append(node.tail)
        return texts

    # Join all texts into one single text string
    text = ' '.join(filter(None, extract([xml])))

    lines = []
    for line in text.splitlines():
        words = [w.strip() for w in line.split()]
        lines.append(' '.join(filter(None, words)))
    text = '\n\n'.join(filter(None, lines))

    return text


def itermatches(matches):
    a, b = tee(matches)
    tail = None
    match = next(b)
    yield None, match.string[0:match.start()]
    for match, tail in zip(a, b):
        yield match, match.string[match.end():tail.start()]
    if tail:
        yield tail, tail.string[tail.end():]


def parse_parentheses(text):
    match = re.search(r'^\s*\(([^)]+)\)\s*\.', text, flags=re.MULTILINE)
    if match:
        content = match.group(1)
        return match.string[match.end():].strip(), [x.strip() for x in content.split(',')]
    return text, None


def parse_match(match, tail, emphasis, date, chairman):
    data = {}

    time_match = re.search(r'(\d+)\.(\d+) val\.', match.group())
    if time_match:
        data['time'] = '%s:%s' % (time_match.group(1), time_match.group(2))
        data['text'] = tail.strip()
    elif match.group().isupper() and match.group() in emphasis:
        tail, parens = parse_parentheses(tail)
        data['speaker'] = match.group()
        data['text'] = tail.strip()
        data['parens'] = parens

        # Frakcija
        data['parliamentary_group'] = None
        parliamentary_group_index = None
        for i, paren in enumerate(data['parens'] or []):
            if is_parliamentary_group(paren):
                data['parliamentary_group'] = paren
                parliamentary_group_index = i
                break
        if parliamentary_group_index is not None:
            del data['parens'][i]

        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        data['position'] = None

        # Primininko vardas
        data['pirmininkas'] = None
        if data['speaker'].startswith('PIRMININK'):
            data['position'] = 'pirmininkas'
        if data['position'] == 'pirmininkas' and len(data['parens'] or []) == 1:
            data['pirmininkas'] = chairman = data['parens'][0]
            data['parens'] = None

        data['vardas'] = None
        data['pavardė'] = None
        if data['position'] == 'pirmininkas':
            if chairman is not None:
                found = find_mp(chairman, date)
            else:
                found = find_chairman(date)
            if found:
                data['vardas'] = found['vardas']
                data['pavardė'] = found['pavardė']

        if data['position'] is None:
            mp = find_mp(data['speaker'], date)
            if mp:
                data['position'] = 'seimo narys'
                data['vardas'] = mp['vardas']
                data['pavardė'] = mp['pavardė']
    else:
        data['text'] = match.group() + tail
    return data


def extract_surname(value):
    name = value.replace('.', ' ').strip() if value else ''
    return name.split()[-1].upper()


speaker_re = re.compile(r'''
^\s*\d+\.\d+\ val\.$|
^PIRMININK(AS|Ė)\b\.?|
^\w\.\s*\w\.\s*\w\.\s*[\w-]+\b\.?|
^\w\.\s*\w\.\s*[\w-]+\b\.?|
^\w\.\s*[\w-]+\b\.?
''', flags=re.UNICODE | re.MULTILINE | re.VERBOSE)


def clean_empahsis_text(text):
    """
    >>> clean_empahsis_text('PIRMININKĖ (R. BAŠKIENĖ')
    'PIRMININKĖ'

    >>> clean_empahsis_text('PIRMININKAS.')
    'PIRMININKAS.'

    >>> clean_empahsis_text('PIRMININKAS (V. PAVARDENIS, FRAK).')
    'PIRMININKAS'
    """
    text = text.strip()
    match = speaker_re.search(text)
    if match:
        return match.group()


@func()
def parse(row):
    tree = lxml.etree.fromstring(row.value['docbook'].replace('\n', ' ').encode('utf-8'))
    text = extract_text(tree)
    emphasis = set(filter(None, map(clean_empahsis_text, tree.xpath('//emphasis/text()'))))

    result = []
    chairman = None
    matches = speaker_re.finditer(text)
    matches = itermatches(matches)
    _, tail = next(matches, (None, ''))
    for match, tail in matches:
        try:
            data = parse_match(match, tail, emphasis, row.value['date'], chairman)
            if data.get('pirmininkas') is not None:
                chairman = data['pirmininkas']
            result.append(data)
        except:
            print(row.key)
            pprint(dict(row.value, docbook=None, match=match.group(), tail=tail))
            with open('/tmp/stenograma.xml', 'w') as f:
                f.write(row.value['docbook'])
            with open('/tmp/stenograma.txt', 'w') as f:
                f.write(text)
            raise

    params = {
        'source': row.value['source'],
        'date': row.value['date'],
        'time': next((x['time'] for x in result if 'time' in x), None),
        'speaker': None,
        'text': '',
        'parens': None,
        'emphasis': False,
        'parliamentary_group': None,
        'position': None,
        'vardas': None,
        'pavardė': None,
        'pirmininkas': None,
        'rowno': 0,
    }
    for data in result:
        try:
            if data.get('speaker'):
                if params['speaker'] is not None:
                    params['rowno'] += 1
                    yield row.key, {k: v for k, v in params.items() if k != 'parens'}
                params = dict(params, **data)
            else:
                data['text'] = params['text'] + '\n\n' + data['text']
                params = dict(params, **data)
        except:
            pprint(params)
            with open('/tmp/stenograma.xml', 'w') as f:
                f.write(row.value['docbook'])
            with open('/tmp/stenograma.txt', 'w') as f:
                f.write(text)
            raise

    if params['speaker'] is not None:
        params['rowno'] += 1
        yield row.key, {k: v for k, v in params.items() if k != 'parens'}


def get_chairmans():
    # Seimo pirmininkų sąrašas
    # Šaltinis: https://query.wikidata.org/
    #
    # SELECT DISTINCT ?s ?nameLabel ?surnameLabel ?start ?end WHERE {
    #   ?s p:P39 ?stm .
    #   ?stm ps:P39 wd:Q12663218 ; pq:P580 ?start .
    #   OPTIONAL { ?stm pq:P582 ?end . }
    #   OPTIONAL { ?s wdt:P735 ?name . }
    #   OPTIONAL { ?s wdt:P734 ?surname . }
    #   SERVICE wikibase:label { bd:serviceParam wikibase:language "lt" . }
    # }
    # ORDER BY ?start

    chairmans = [
        {'wd': 'Q164582', 'name': 'Vytautas', 'surname': 'Landsbergis', 'start': '1990-03-10', 'end': '1992-11-22'},
        {'wd': 'Q212751', 'name': 'Algirdas', 'surname': 'Brazauskas', 'start': '1992-11-24', 'end': '1993-02-14'},
        {'wd': 'Q341349', 'name': 'Česlovas', 'surname': 'Juršėnas', 'start': '1993-02-14', 'end': '1996-11-22'},
        {'wd': 'Q164582', 'name': 'Vytautas', 'surname': 'Landsbergis', 'start': '1996-11-26', 'end': '2000-10-18'},
        {'wd': 'Q356704', 'name': 'Artūras', 'surname': 'Paulauskas', 'start': '2000-10-19', 'end': '2004-04-06'},
        {'wd': 'Q341349', 'name': 'Česlovas', 'surname': 'Juršėnas', 'start': '2004-04-20', 'end': '2004-07-11'},
        {'wd': 'Q356704', 'name': 'Artūras', 'surname': 'Paulauskas', 'start': '2004-07-12', 'end': '2006-04-11'},
        {'wd': 'Q1376549', 'name': 'Viktoras', 'surname': 'Muntianas', 'start': '2006-04-13', 'end': '2008-03-31'},
        {'wd': 'Q341349', 'name': 'Česlovas', 'surname': 'Juršėnas', 'start': '2008-04-01', 'end': '2008-11-17'},
        {'wd': 'Q719281', 'name': 'Arūnas', 'surname': 'Valinskas', 'start': '2008-11-17', 'end': '2009-09-15'},
        {'wd': 'Q270360', 'name': 'Irena', 'surname': 'Degutienė', 'start': '2009-09-15', 'end': '2012-11-16'},
        {'wd': 'Q556431', 'name': 'Vydas', 'surname': 'Gedvilas', 'start': '2012-11-16', 'end': '2013-10-03'},
        {'wd': 'Q774843', 'name': 'Loreta', 'surname': 'Graužinienė', 'start': '2013-10-03', 'end': '2013-12-31'},
        {'wd': 'Q27537241', 'name': 'Viktoras', 'surname': 'Pranckietis', 'start': '2016-11-14'},
    ]

    chairmans = pd.DataFrame(chairmans)
    chairmans['start'] = pd.to_datetime(chairmans.start)
    chairmans['end'] = pd.to_datetime(chairmans.end)
    return chairmans.rename(columns={
        'name': 'vardas',
        'surname': 'pavardė',
    })


def get_seimonariai_and_pareigos(bot, kadencijos):
    seimonariai = {
        'kadencija': [],
        'p_asm_id': [],
        'vardas': [],
        'pavardė': [],
        'gimė': [],
        'nuo': [],
        'iki': [],
    }
    pareigos = {
        'p_asm_id': [],
        'p_pad_id': [],
        'nuo': [],
        'iki': [],
        'pareigos': [],
        'padalinys': [],
        'tipas': [],
    }
    for kadencija in kadencijos:
        for row in bot.pipe('%d/seimo-nario-duomenys' % kadencija).rows():
            try:
                seimonariai['kadencija'].append(kadencija)
                seimonariai['p_asm_id'].append(row.value['p_asm_id'])
                seimonariai['vardas'].append(row.value['vardas'])
                seimonariai['pavardė'].append(row.value['pavardė'].upper())
                seimonariai['gimė'].append(row.value['gimė'])
                seimonariai['nuo'].append(row.value['mandatas']['nuo'])
                seimonariai['iki'].append(row.value['mandatas']['iki'])

                for frakcija in row.value.get('frakcijos', []):
                    pareigos['p_asm_id'].append(row.value['p_asm_id'])
                    pareigos['p_pad_id'].append(frakcija.get('p_pad_id'))
                    pareigos['nuo'].append(frakcija['nuo'])
                    pareigos['iki'].append(frakcija['iki'])
                    pareigos['pareigos'].append(frakcija['pareigos'])
                    pareigos['padalinys'].append(frakcija['frakcija'])
                    pareigos['tipas'].append('Frakcijose')

                for pareiga in row.value['pareigos']:
                    pareigos['p_asm_id'].append(row.value['p_asm_id'])
                    pareigos['p_pad_id'].append(pareiga.get('p_pad_id'))
                    pareigos['nuo'].append(pareiga['nuo'])
                    pareigos['iki'].append(pareiga['iki'])
                    pareigos['pareigos'].append(pareiga['pareigos'])
                    pareigos['padalinys'].append(pareiga.get('pavadinimas', pareiga.get('padalinys')))
                    pareigos['tipas'].append(pareiga.get('tipas'))
            except:
                print('kadencija:', kadencija)
                print(row.key)
                pprint(row.value)
                raise

    seimonariai = pd.DataFrame(seimonariai)
    pareigos = pd.DataFrame(pareigos)

    seimonariai['nuo'] = pd.to_datetime(seimonariai['nuo'])
    seimonariai['iki'] = pd.to_datetime(seimonariai['iki'])

    return seimonariai, pareigos


def initializer(bot):
    global CHAIRMANS, SEIMONARIAI, PAREIGOS

    kadencijos = [1990, 1992, 1996, 2000, 2004, 2008, 2012, 2016]
    for kadencija in kadencijos:
        bot.define('%d/seimo-nario-duomenys' % kadencija, 'data/lrs/seimonariai.db')

    CHAIRMANS = get_chairmans()
    SEIMONARIAI, PAREIGOS = get_seimonariai_and_pareigos(bot, kadencijos)


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']['www.lrs.lt']


pipeline = {
    'pipes': [
        define('posėdžių-puslapiai', botlib.dburi('lrs/posedziai')),
        define('stenogramų-sąrašas'),
        define('stenogramų-puslapiai', compress=True),
        define('metadata'),
        define('dokumentai', compress=True),
        define('docbook', compress=True),
        define('stenogramos', compress=True),
    ],
    'tasks': [

        # Nuorodos į stenogramų puslapius
        task('posėdžių-puslapiai', 'stenogramų-sąrašas').select(
            '.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href',
            check='.fakt_pos > .list.main li > a',
        ).dedup(),
        task('stenogramų-sąrašas', 'stenogramų-puslapiai').download(cookies=cookies, check=(
            '.legalActHeaderTable xpath:.//td[text() = "Rūšis:"]'
        )),

        # Stenogramų puslapio meta duomenys
        task('stenogramų-puslapiai', 'metadata').select(this.key, {
            'url': this.value.url,
            'rūšis': select('.legalActHeaderTable xpath:.//td[text() = "Rūšis:"]/following-sibling::td[1]').text(),
            'dokumento nr.': select('.legalActHeaderTable xpath:.//td[text() = "Dokumento nr.:"]/following-sibling::td[1]').text(),
            'reg. data': select('.legalActHeaderTable xpath:.//td[text() = "Reg. data:"]/following-sibling::td[1]').text(),
            'parengė': select('.legalActHeaderTable xpath:.//td[text() = "Parengė:"]/following-sibling::td[1]').text(),
            'paskelbta': select('.legalActHeaderTable xpath:.//td[text() = "Paskelbta:"]/following-sibling::td[1]').text(),
            'eurovoc terminai': select('.legalActHeaderTable xpath:.//td[text() = "Eurovoc terminai: "]/following-sibling::td[1]').text(),
            'kalba': select('.legalActHeaderTable xpath:.//td[text() = "Kalba:"]/following-sibling::td[1]').text(),
            'būsena': select('.legalActHeaderTable xpath:.//td[text() = "Būsena:"]/following-sibling::td[1]').text(),
            'ryšys su es teisės aktais': select('.legalActHeaderTable xpath:.//td[text() = "Ryšys su ES teisės aktais:"]/following-sibling::td[1]').text(),
            'html iframe url': select('.docPanel .legalActIFrameWrapper iframe@src?'),
            'attachments': [select('.centerHeader xpath:./a[contains(@href, "/format/")]/@href')],
            'attachment': select(['.centerHeader xpath:./a[contains(@href, "/format/")]/@href']).apply(attachment),
        }),
        task('metadata').export('data/lrs/stenogramos/metadata.csv'),

        # Atsisiunčiame prisegtus dokumentų failus (doc, docx formatais)
        task('metadata', 'dokumentai').download(this.value.attachment, cookies=cookies, update={
            'date': this.value['reg. data'],
            'source': this.key,
        }),

        # Convertuojame doc, docx failus į docbook formatą
        task('dokumentai', 'docbook').select(this.key, {
            'filename': this.value.headers['Content-Disposition'].header().filename,
            'mimetype': this.value.headers['Content-Type'].header().value,
            'docbook': this.value.content.apply(xtodocbook, this.value.headers['Content-Type'].header().value),
            'source': this.value.source,
            'date': this.value.date,
        }),

        task('stenogramos').clean(),
        task('docbook', 'stenogramos').reset().select(parse(this)),
    ],
}


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        import doctest
        result = doctest.testmod()
        if result.failed:
            print(result)
            sys.exit(1)

        bot = Bot('data/lrs/stenogramos.db', verbosity=1).autodefine()
        initializer(bot)

        output = 'text'
        key = 'https://e-seimas.lrs.lt/rs/legalact/TAK/TAIS.76973/format/MSO2010_DOCX/'

        if output == 'table':
            result = bot.commands.select(bot.pipe('docbook'), query=parse(this), key=key, table=False, raw=True)

            import collections
            frame = pd.DataFrame([collections.OrderedDict([
                ('date', row.value['date']),
                ('time', row.value['time']),
                ('rowno', row.value['rowno']),
                ('vardas', row.value['vardas']),
                ('pavardė', row.value['pavardė']),
                ('group', row.value['parliamentary_group']),
                ('speaker', row.value['speaker']),
                ('position', row.value['position']),
                ('pirmininkas', row.value['pirmininkas']),
                ('emphasis', row.value['emphasis']),
            ]) for row in result])

            pd.set_option('display.width', 300)
            pd.set_option('display.max_rows', 1000)
            print(frame)

        else:
            result = bot.commands.select(bot.pipe('docbook'), query=parse(this), key=key, table=False, raw=True)

            import textwrap
            for row in result:
                print('{date} {time}: {speaker} ({parliamentary_group}), {vardas} {pavardė}, {position}'.format(**row['value']))
                print()
                for p in row['value']['text'].splitlines():
                    print('  ' + '\n  '.join(textwrap.wrap(p)))
                print()
    else:
        botlib.runbot(pipeline, initializer)
