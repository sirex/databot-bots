#!/usr/bin/env python3

import datetime
import botlib

from databot import define, select, task
from databot.handlers.html import Call


def normtime(val):
    return datetime.datetime.strptime(val, '%Y-%m-%d-%H-%M').strftime('%Y-%m-%dT%H-%M')


class key(Call):

    def __init__(self, *queries):
        self.queries = queries

    def __call__(self, select, row, node, many=False, single=True):
        return '/'.join([
            normtime(select.render(row, node, q, many, single))
            for q in self.queries
        ])


pipeline = {
    'pipes': [
        define('pages', compress=True),
        define('data'),
    ],
    'tasks': [
        task('pages').freq(minutes=5).download('http://www.meteo.lt/lt_LT/miestas?placeCode=Vilnius'),
        task('pages', 'data').select([
            '.forecast-hours', (
                key(select(['xpath://body css:.forecast-hours .forecastTime:text']).min(),
                    select('.forecastTime:text')),
                {
                    'base': select(['xpath://body css:.forecast-hours .forecastTime:text']).min().apply(normtime),  # precision=hours base time
                    'time': select('.forecastTime:text').apply(normtime),  # precision=hours prediction time
                    'temperature': select('.temperature:text').cast(int),  # °C
                    'wind_direction': select('.windDirectionGroundDegree:text').cast(int),  # degrees
                    'wind_speed': select('.windSpeedGround:text').cast(int),  # m/s
                    'gust_speed': select('.windGustGround:text').cast(int),  # m/s
                    'precipitation': select('.precipitation:text').cast(float),  # mm/h
                    'pressure': select('.pressureMeanSea:text').cast(int),  # hPa
                    'humidity': select('.humidityGround:text').cast(int),  # %
                    'feels_like': select('.feelLike:text').cast(int),  # °C
                }
            )
        ]).compact(),
        task('data').export('data/meteo/meteo.tsv'),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
