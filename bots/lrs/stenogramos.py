#!/usr/bin/env python3

import os
import botlib
import yaml

from subprocess import run, PIPE
from tempfile import NamedTemporaryFile

from databot import define, select, task, this


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
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
