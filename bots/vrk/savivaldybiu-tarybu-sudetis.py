#!/usr/bin/env python3

import botlib
import functools

from databot import call, value, first, join


@functools.lru_cache()
def get_first_names():
    return {v['name'].lower() for v in botlib.getbot('vlkk/vardai').pipe('vardų sąrašas').data.values()}


def split_first_last_name(names):
    first_name = []
    last_name = []
    first_names = get_first_names()
    for name in names:
        if name.lower() in first_names:
            first_name.append(name)
        else:
            last_name.append(name)

    if not first_name:
        raise ValueError('Could not detect first name for "%s".' % ' '.join(names))

    return ' '.join(first_name), ' '.join(last_name)


def fix_municipality_names(name):
    return {
        'Palangos savivaldybės taryba': 'Palangos miesto savivaldybės taryba',
    }.get(name, name)


def split_name(data):
    names = data.pop('pavardė vardas').strip().split()

    if data['kadencija'] == 2015:
        if names[-1] in ('(MERAS)', '(MERĖ)'):
            meras = True
            names = names[:-1]
        else:
            meras = False
    else:
        meras = None

    assert len(names) > 1

    names = [n.title() for n in names]

    if len(names) > 2:
        first_name, last_name = split_first_last_name(names)
    else:
        last_name, first_name = names

    data['meras'] = meras
    data['vardas'] = first_name
    data['pavardė'] = last_name

    return data


def define(bot):
    bot.define('savivaldybių rinkimai 2007')
    bot.define('savivaldybių sąrašo puslapiai 2007')
    bot.define('savivaldybių rezultatų nuorodos 2007')
    bot.define('savivaldybių rezultatų puslapiai 2007')

    bot.define('savivaldybių rinkimai 2011')
    bot.define('savivaldybių sąrašo puslapiai 2011')
    bot.define('savivaldybių rezultatų nuorodos 2011')
    bot.define('savivaldybių rezultatų puslapiai 2011')

    bot.define('savivaldybių rinkimai')
    bot.define('savivaldybių sąrašo puslapiai')
    bot.define('savivaldybių rezultatų nuorodos')
    bot.define('savivaldybių rezultatų puslapiai')
    bot.define('tarybos nariai')


def run(bot):

    if bot.run('2007'):
        start_url = 'http://www.vrk.lt/statiniai/puslapiai/2007_savivaldybiu_tarybu_rinkimai/lt/savivaldybes.html'
        with bot.pipe('savivaldybių rinkimai 2007').append(start_url).dedup():
            with bot.pipe('savivaldybių sąrašo puslapiai 2007').download():
                with bot.pipe('savivaldybių rezultatų nuorodos 2007').select(['table.partydata tr td b > a@href']).dedup():  # noqa
                    with bot.pipe('savivaldybių rezultatų puslapiai 2007').download():
                        bot.pipe('tarybos nariai').select(join(
                            [
                                'xpath://table[contains(@class,"partydata")][1]/tbody/tr[count(td)=3]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': first('tr > td[3]:text', value('2007-03-04')),
                                        'iki': value('2011-02-26'),
                                        'mandato panaikinimo priežastis': value(None),
                                        'savivaldybė': call(fix_municipality_names, '/font[size="5"] > b:text'),
                                        'kadencija': value(2007),
                                    })
                                )
                            ],
                            [
                                'xpath://table[contains(@class,"partydata")][2]/tbody/tr[count(td)=5]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': first('tr > td[3]:text', value('2007-03-04')),
                                        'iki': first('tr > td[4]:text', value('2011-02-26')),
                                        'mandato panaikinimo priežastis': 'tr > td[5]:text',
                                        'savivaldybė': call(fix_municipality_names, '/font[size="5"] > b:text'),
                                        'kadencija': value(2007),
                                    })
                                )
                            ],
                        ))

    if bot.run('2011'):
        start_url = 'http://www.2013.vrk.lt/2011_savivaldybiu_tarybu_rinkimai/output_lt/savivaldybiu_tarybu_sudetis/savivaldybes.html'  # noqa
        with bot.pipe('savivaldybių rinkimai 2011').append(start_url).dedup():
            with bot.pipe('savivaldybių sąrašo puslapiai 2011').download():
                with bot.pipe('savivaldybių rezultatų nuorodos 2011').select(['table.partydata tr td b > a@href']).dedup():  # noqa
                    with bot.pipe('savivaldybių rezultatų puslapiai 2011').download():
                        bot.pipe('tarybos nariai').select(join(
                            [
                                'xpath://table[contains(@class,"partydata")][1]/tr[count(td)=3]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': first('tr > td[3]:text', value('2011-02-27')),
                                        'iki': value('2015-02-28'),
                                        'mandato panaikinimo priežastis': value(None),
                                        'savivaldybė': call(fix_municipality_names, '/font[size="5"] > b:text'),
                                        'kadencija': value(2011),
                                    })
                                )
                            ],
                            [
                                'xpath://table[contains(@class,"partydata")][2]/tr[count(td)=5]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': first('tr > td[3]:text', value('2011-02-27')),
                                        'iki': first('tr > td[4]:text', value('2015-02-28')),
                                        'mandato panaikinimo priežastis': 'tr > td[5]:text',
                                        'savivaldybė': call(fix_municipality_names, '/font[size="5"] > b:text'),
                                        'kadencija': value(2011),
                                    })
                                )
                            ],
                        ))

    if bot.run('2015'):
        start_url = 'http://www.2013.vrk.lt/2015_savivaldybiu_tarybu_rinkimai/output_lt/savivaldybiu_tarybu_sudetis/savivaldybes.html'  # noqa
        with bot.pipe('savivaldybių rinkimai').append(start_url).dedup():
            with bot.pipe('savivaldybių sąrašo puslapiai').download():
                with bot.pipe('savivaldybių rezultatų nuorodos').select(['table.partydata tr td b > a@href']).dedup():
                    with bot.pipe('savivaldybių rezultatų puslapiai').download():
                        bot.pipe('tarybos nariai').select(join(
                            [
                                'xpath://table[contains(@class,"partydata3")][1]/tr[count(td)>0]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': 'tr > td[3]:text',
                                        'iki': value('2019-03-01'),
                                        'mandato panaikinimo priežastis': value(None),
                                        'savivaldybė': '/font[size="5"] > b:text',
                                        'kadencija': value(2015),
                                    })
                                )
                            ],
                            [
                                'xpath://table[contains(@class,"partydata3")][2]/tr[count(td)>0]', (
                                    'tr > td[2] > a@href', call(split_name, {
                                        'sąrašas': 'tr > td[1]:text',
                                        'pavardė vardas': 'tr > td[2] > a:text',
                                        'nuo': 'tr > td[3]:text',
                                        'iki': 'tr > td[4]:text',
                                        'mandato panaikinimo priežastis': 'tr > td[5]:text',
                                        'savivaldybė': '/font[size="5"] > b:text',
                                        'kadencija': value(2015),
                                    })
                                )
                            ],
                        ))

    bot.compact()

    bot.pipe('tarybos nariai').export('data/vrk/savivaldybiu-tarybu-sudetis/tarybos-nariai.csv')


if __name__ == '__main__':
    botlib.runbot(define, run)
