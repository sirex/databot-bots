#!/usr/bin/env python3

import yaml
import botlib

from databot import define, task, this, call, strip


with open('settings.yml') as f:
    settings = yaml.load(f)

cookies = settings['cookies']['www.lrs.lt']

pipeline = {
    'pipes': [
        define('klausimų-puslapiai', botlib.dburi('lrs/posedziai')),
        define('dokumentų-sąrašas'),
        define('dokumentų-puslapiai', compress=True),
        define('susijusių-dokumentų-sąrašas'),
        define('susijusių-dokumentų-puslapiai', compress=True),
        define('metadata'),
        define('texts'),
    ],
    'tasks': [
        task('klausimų-puslapiai', 'dokumentų-sąrašas').
        select(['#page-content div.default b xpath:a[text()="dokumento tekstas"]/@href']).
        dedup(),

        task('dokumentų-sąrašas', 'dokumentų-puslapiai').
        download(cookies=cookies, check='#page-content div.default b xpath:a[text()="dokumento tekstas"]'),

        task('dokumentų-puslapiai', 'susijusių-dokumentų-sąrašas').
        select(['#page-content div.default b xpath:a[text()="susiję dokumentai"]/@href']).
        dedup(),

        task('susijusių-dokumentų-puslapiai').
        download(cookies=cookies, check='#page-content div.default b xpath:a[text()="susiję dokumentai"]'),

        task('dokumentų-puslapiai', 'metadata').
        select(this.key, call(dict, ['.basic .ltb', (strip(':text'), strip('b:text?'))])).
        dedup(),

        task('dokumentų-puslapiai', 'texts').
        select(this.key, 'body > div:content').
        dedup(),

        task('metadata').export('data/lrs/dokumentai/metadata.csv', include=[
            'key',
            'Data:',
            'Rūšis:',
            'Kalba:',
            'Numeris:',
            'Statusas:',
        ]),

        task('texts').export('data/lrs/dokumentai/texts.csv', include=[
            'key',
            'value',
        ]),

        task().compact(),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
