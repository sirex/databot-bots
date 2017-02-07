#!/usr/bin/env python3

import os
import botlib

from databot import define, select, task, this

cookies = {
    'incap_ses_473_791905': os.environ['INCAP_SES'],
}

pipeline = {
    'pipes': [
        define('posėdžių-puslapiai', botlib.dburi('lrs/balsavimai')),
        define('stenogramų-sąrašas'),
        define('stenogramų-puslapiai', compress=True),
        define('metadata'),
    ],
    'tasks': [

        # Nuorodos į stenogramų puslapius
        task('posėdžių-puslapiai', 'stenogramų-sąrašas').select(
            '.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href',
            check='.fakt_pos > .list.main li > a',
        ).dedup(),
        task('stenogramų-sąrašas', 'stenogramų-puslapiai').download(cookies=cookies),

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
            # 'iframe link': select('.legalActIFrameWrapper'),
        }),
        task('metadata').export('data/lrs/stenogramos/metadata.csv'),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
