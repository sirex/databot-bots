#!/usr/bin/env python3

import os
import botlib

from databot import define, select, task, this

cookies = {
    # Norint apeiti Incapsula apsaugą, reikia naršyklėje suvesti
    # paveiksliuke rodomą apsaugos kodą ir nusikopijuoti incap_ses_*
    # sausainiukus.
    #
    # Leidžians skriptą serveryje, naržyklę reikia leisti per serverio
    # proxy. Serverio SOCS proxy galima įjungti taip:
    #
    #   ssh -D 8080 remote-server
    #
    # SOCKS proxy nustatymai naršyklėje: 127.0.0.1:8080
    #
    # Before running this bot run:
    #
    #   export incap_ses=""
    'incap_ses_473_791905': os.environ['incap_ses'],
}

# https://e-seimas.lrs.lt/portal/legalAct/lt/TAK/c61cd711d98711e69c5d8175b5879c31
#                            /rs/legalact/lt/TAK/c61cd711d98711e69c5d8175b5879c31/

pipeline = {
    'pipes': [
        define('posėdžių-puslapiai', botlib.dburi('lrs/balsavimai')),
        define('stenogramų-sąrašas'),
        define('stenogramų-puslapiai'),
        define('metadata'),
    ],
    'tasks': [

        # Nuorodos į stenogramų puslapius
        task('posėdžių-puslapiai', 'stenogramų-sąrašas').select(
            '.fakt_pos ul.list > li xpath:a[text()="Stenograma"]/@href',
            check='.fakt_pos > .list.main li > a',
        ).dedup(),
        task('stenogramų-sąrašas', 'stenogramų-puslapiai').download(),

        # Stenogramų puslapio meta duomenys
        task('stenogramų-puslapiai', 'metadata').select(this.key, {
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
