#!/usr/bin/env python3

import json
import botlib
import pandas as pd
import pathlib

from subprocess import run
from functools import partial
from tempfile import TemporaryDirectory
from databot import define, task, select, this


def read_csv(filename, key, names, row):
    with TemporaryDirectory() as tempdir:
        tempdir = pathlib.Path(tempdir)
        zipfile = tempdir / 'data.zip'
        with zipfile.open('wb') as f:
            f.write(row.value['content'])
        run(['unzip', str(zipfile)], cwd=str(tempdir), check=True)
        data = pd.read_csv(
            str(tempdir / filename),
            sep=r';\s*',
            engine='python',
            encoding='iso-8859-4',
            decimal=',',
            skiprows=12,
            comment=';',
            header=None,
            names=names,
        )

    yield from ((str(x[key]), json.loads(x.to_json())) for _, x in data.iterrows())


pipeline = {
    'pipes': [
        define('vidurkiai-zip'),
        define('skaiciai-zip'),
        define('vidurkiai'),
        define('skaiciai'),
        define('imones-puslapis', compress=True),
        define('imones'),
    ],
    'tasks': [
        task('vidurkiai-zip').monthly().download('http://sodra.is.lt/Failai/Vidurkiai.zip'),
        task('vidurkiai-zip', 'vidurkiai').
            call(partial(read_csv, 'VIDURKIAI.CSV', 'kodas', ['regnr', 'kodas', 'alga', 'autorine', 'viso'])).
            dedup(),
        task('skaiciai-zip').monthly().download('http://sodra.is.lt/Failai/Apdraustuju_skaicius.zip'),
        task('skaiciai-zip', 'skaiciai').
            call(partial(read_csv, 'APDRAUSTUJU_SKAICIUS.CSV', 'kodas', ['regnr', 'kodas', 'skaicius'])).
            dedup(),
        task('vidurkiai', 'imones-puslapis').download(
            'https://draudejai.sodra.lt/draudeju_viesi_duomenys/',
            method='POST',
            data={
                'formType': 'NEW',
                'year': '2017',
                'month': '1',
                'declarantCode2': this.value.kodas.cast(int).cast(str),
                'actionName': 'MEAN',
            },
            check='xpath://td[text() = "Draudėjo pavadinimas"]',
        ),
        task('imones-puslapis', 'imones').select(this.value.request.data.declarantCode2, {
            'pavadinimas': select('xpath://td[text() = "Draudėjo pavadinimas"]/following-sibling::td[1]/text()'),
        })
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
