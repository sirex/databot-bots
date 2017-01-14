#!/usr/bin/env python3

import botlib

from datetime import timedelta
from databot import define, task, this, strip


pipeline = {
    'pipes': [
        define('index urls'),
        define('index pages'),
        define('dataset urls'),
        define('dataset pages'),
        define('dataset data'),
        define('datasets'),
    ],
    'tasks': [
        task('index urls').clean(timedelta(days=1)),
        task('index urls').append('http://opendata.gov.lt/index.php?vars=/public/public/search').dedup(),
        task('index urls', 'index pages').download(),
        task('index pages', 'index urls').select(['td > a.path@href']).dedup(),
        task('index pages', 'dataset urls').reset().select(['form[name=frm] > table > tr > td[3] > a@href']),
        task('dataset urls').clean(timedelta(days=7)).dedup(),
        task('dataset urls', 'dataset pages').download(),
        task('dataset pages', 'dataset data').select(this.key, [
            'table xpath:tr[count(td)=2]', (
                'td[1]:content',
                strip('td[2]:content'),
            )
        ]),
        task('dataset data').clean(timedelta(days=7)).dedup(),
        task('dataset data', 'datasets').call(lambda x: [(x.key, dict(x.value))]),
        task('datasets').export('data/ivpk/opendata-gov-lt/datasets.jsonl'),
        task().compact(),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
