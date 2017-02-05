#!/usr/bin/env python3

import re
import json
import botlib

from databot import define, task, select, this


def populiarumas(value):
    tops = re.search(r'var tops = (\{[^}]+\});', value.decode())
    data = re.search(r'data: (\[[^\]]+\])', value.decode())
    assert tops
    assert data
    tops = {int(k): int(v) if v else 0 for k, v in json.loads(tops.group(1)).items()}
    data = json.loads(data.group(1))
    assert len(tops) == len(data)
    data = dict(zip(sorted(tops.keys()), data))
    return {
        'year': data,
        'mean': sum(data.values()) / len(data),
        'max': max(data.values()),
        'top': min(tops.values())
    }


pipeline = {
    'pipes': [
        define('raidės-nuorodos'),
        define('raidės-puslapiai', compress=True),
        define('sąrašas-nuorodos'),
        define('sąrašas-puslapiai', compress=True),
        define('vardai-nuorodos'),
        define('vardai-puslapiai', compress=True),
        define('vardai'),
    ],
    'tasks': [
        # Vardo pirmos raidės sąrašas
        task('raidės-nuorodos').monthly().append('https://www.tevu-darzelis.lt/vaiku-vardai/A/'),
        task('raidės-puslapiai', 'raidės-nuorodos', watch=True).select(['#alphabet li a@href']).dedup(),
        task('raidės-nuorodos', 'raidės-puslapiai', watch=True).download(),

        # Sąrašo puslapiavimas
        task('raidės-puslapiai', 'sąrašas-nuorodos', watch=True).select(['.pagination li a@href']).dedup(),
        task('sąrašas-puslapiai', 'sąrašas-nuorodos', watch=True).select(['.pagination li a@href']).dedup(),
        task('sąrašas-nuorodos', 'sąrašas-puslapiai', watch=True).download(),

        # Vardų puslapiai
        task('sąrašas-puslapiai', 'vardai-nuorodos').select([
            '.name-list li', (
                'a@href', {
                    'name': select('a').text(),
                    'class': select('a@class'),
                }
            )
        ]).dedup(),
        task('vardai-nuorodos', 'vardai-puslapiai').download(),

        # Vardai
        task('vardai-puslapiai', 'vardai').select(this.key.urlparse().path, {
            'lytis': select('#page-left xpath:.//h1[1]/@class'),
            'vardas': select('#page-left xpath:.//h1[1]/strong/text()'),
            'kilmė': select('#name-info xpath:./p[strong/text() = "Vardo kilmė:"]/text()?').null().strip(),
            'vardadienis': select('#name-info xpath:./p[strong/text() = "Vardadienis:"]/text()?').null().replace('\xa0', ' ').strip(),
            'reikšmė': select('#name-info xpath:./p[strong/text() = "Vardo reikšmė:"]?').null().text(exclude=['xpath:./strong[1]']),
            'panašūs vardai': ['#name-info xpath:./p[strong/text() = "Panašūs ir giminingi vardai:"]/a/text()'],
            'populiarumas': this.value.content.apply(populiarumas),
        }),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
