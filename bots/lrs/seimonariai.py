#!/usr/bin/env python3

import os
import botlib

from databot import define, select, task, this


envvars = {'incap_ses_108_791905', 'incap_ses_473_791905'}
cookies = {x: os.environ[x] for x in envvars if x in os.environ}

pipeline = {
    'pipes': [
        define('pirmas-puslapis', compress=True),
        define('sąrašas'),
        define('nuotraukos'),
    ],
    'tasks': [
        task('pirmas-puslapis').monthly().download(
            'http://www.lrs.lt/sip/portal.show?p_r=8801&p_k=1&filtertype=0', cookies=cookies, check='.smn-list',
        ),

        # Seimo narių sąrašas
        task('pirmas-puslapis', 'sąrašas').select([
            '.smn-list .list-member', (
                'a.smn-name@href', {
                    'vardas': select('a.smn-name:text'),
                    'pavarde': select('a.smn-name > span.smn-pavarde:text'),
                    'nuotrauka': select('.smn-big-photo img@src'),
                },
            ),
        ]),

        # Nuotraukos
        task('sąrašas', 'nuotraukos').download(this.value.nuotrauka, cookies=cookies)
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
