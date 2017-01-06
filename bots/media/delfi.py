#!/usr/bin/env python3

import botlib
import databot


def define(bot):
    bot.define('archyvas', botlib.dburi('media/delfi/archyvas', create=True), compress=True)
    bot.define('archyvo-nuorodos')
    bot.define('archyvo-straipsnių-nuorodos')
    bot.define('straipsniai', botlib.dburi('media/delfi/straipsniai', create=True), compress=True)
    bot.define('straipsnių-tekstai', compress=True)


def init(bot):
    archive = bot.pipe('archyvas')
    urls = bot.pipe('archyvo-nuorodos')

    url = (
        'http://www.delfi.lt/archive/index.php?'
        'fromd=01.01.1999&'
        'tod=01.01.2020&'
        'channel=0&'
        'category=0&'
        'query=&page=%d'
    )
    urls.append(url % i for i in range(1, 9575)).dedup()

    with urls:
        archive.download()


def run(bot):
    init(bot)

    archive = bot.pipe('archyvas')
    urls = bot.pipe('archyvo-straipsnių-nuorodos')
    articles = bot.pipe('straipsniai')
    texts = bot.pipe('straipsnių-tekstai')

    with archive:
        urls.select([
            skip('.arch-search-list > ol > li'), (
                'a.arArticleT@href', {
                    'section': '.search-item-head a.section:text',
                    'date': '.search-item-head > span:text',
                    'title': 'a.arArticleT:text',
                    'comments': 'a.commentCount:text?',
                },
            )
        ])

    with urls:
        articles.download()

    with articles:
        texts.select((
            databot.row.key,
            databot.text('.delfi-article-body', exclude=['.related-box', '.img-article-source']),
        ))


@databot.func()
def skip(nodes):
    return nodes[1:]


if __name__ == '__main__':
    botlib.runbot(define, run)
