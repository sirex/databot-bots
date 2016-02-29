#!/usr/bin/env python3

import botlib

from datetime import timedelta
from databot import row


def define(bot):
    bot.define('index urls')
    bot.define('index pages')
    bot.define('doc urls')
    bot.define('doc pages')


def run(bot):
    start_url = 'http://www.vilnius.lt/vaktai/default.aspx?Id=2&ItemsOnPage=200'
    with bot.pipe('index urls').clean(timedelta(days=1)).append(start_url).dedup():
        while bot.pipe('index pages').is_filled():
            with bot.pipe('index pages').download():
                bot.pipe('index urls').select(['a.paging_text', ('@href', ':text')]).dedup()

    with bot.pipe('index pages'):
        bot.pipe('doc urls').select([
            'a.doc_link_list', (
                '@href', {
                    'title': ':text',
                    'metadata': [
                        'xpath:./ancestor::tr/following-sibling::tr css:.searchResultMetaData xpath:.//text()'
                    ],
                },
            ),
        ])

    with bot.pipe('doc urls').dedup():
        bot.pipe('doc pages').download(update={'source': row.value})

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
