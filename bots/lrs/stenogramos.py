#!/usr/bin/env python3

import os
import botlib

from databot import define, select, task, this


def attachment(value):
    """Select prefered attachment format."""
    formats = [x.split('/')[-2] for x in value]
    for x in ('MSO2010_DOCX', 'MSO2003_DOC'):
        if x in formats:
            return value[formats.index(x)]
    return value[0] if value else None


envvars = {'incap_ses_108_791905', 'incap_ses_473_791905'}
cookies = {x: os.environ[x] for x in envvars if x in os.environ}

pipeline = {
    'pipes': [
        define('posėdžių-puslapiai', botlib.dburi('lrs/posedziai')),
        define('stenogramų-sąrašas'),
        define('stenogramų-puslapiai', compress=True),
        define('metadata'),
        define('dokumentai', compress=True),
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

        task('metadata', 'dokumentai').download(this.value.attachment, cookies=cookies),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
