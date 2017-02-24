#!/usr/bin/env python3

import csv
import botlib
import pathlib
import urllib.parse
import cgi

from databot import call, row
from subprocess import check_call, check_output


def current_git_rev(path: pathlib.Path):
    "Returns current revision hash."
    return check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'])


def gitsync(repo: str, path: pathlib.Path):
    "Returns True if there was new changes and False if there was no changes."
    if path.exists():
        old_rev = current_git_rev(path)
        check_call(['git', '-C', str(path), 'pull'])
        new_rev = current_git_rev(path)
        return old_rev != new_rev
    else:
        check_call(['git', 'clone', repo, str(path)])
        return True


def readcsv(path: pathlib.Path, sep=',', key=None, update=None, limit=float('Inf')):
    update = update or {}
    with path.open() as f:
        reader = csv.DictReader(f, delimiter=sep)
        for i, item in enumerate(reader, 1):
            if i >= limit:
                break
            for k, fn in update.items():
                item[k] = fn(item)
            _key = i if key is None else item.pop(key)
            yield _key, item


def question_url(item):
    return 'http://www.vilnius.lt/l.php?' + urllib.parse.urlencode([
        ('tmpl_into[0]', 'index'),
        ('tmpl_into[1]', 'middle'),
        ('tmpl_name[0]', 'm'),
        ('tmpl_name[1]', 'm_wp2sw_main'),
        ('m', '8'),
        ('itemID', item['MEETING_ID']),
        ('show', 'process'),
        ('qID', item['ID']),
        ('_m_e_id', '11'),
        ('_menu_i_id', '21'),
    ])


def clean_redirect_url(value):
    if value and value.startswith('0;URL='):
        return value[6:]


def attachment_export(item):
    try:
        content_disposition = item.value['headers']['Content-Disposition']
    except KeyError:
        filename = None
        ext = None
    else:
        disposition, params = cgi.parse_header(content_disposition)
        filename = params.get('filename')
        ext = pathlib.Path(filename).suffix if filename else None
    return {
        'attachment-url': item.key,
        'question-url': item.value['question-url'],
        'size': len(item.value['content']),
        'filename': filename,
        'ext': ext,
        'content-type': item.value['headers'].get('Content-Type'),
    }


def define(bot):
    bot.define('questions')
    bot.define('question pages', compress=True)
    bot.define('attachment preview links')
    bot.define('attachment preview', compress=True)
    bot.define('attachment links')
    bot.define('attachments', compress=True)


def run(bot):

    path = pathlib.Path('data/vilnius/vtaryba-git')
    if gitsync('https://github.com/vilnius/taryba.git', path):
        questions = readcsv(path / 'data/questions.csv', sep=';', key='url', update={'url': question_url})
        bot.pipe('questions').append(questions, progress='questions').dedup()

    with bot.pipe('questions'):
        with bot.pipe('question pages').download():
            bot.pipe('attachment preview links').select([
                'a.viewLink xpath:./b[text()="Rodyti kaip HTML"]/..', ('@href', row.key)
            ])
            bot.pipe('attachment links').select([
                '.info_table a.downloadLink', ('@href', {
                    'link-title': 'b:text',
                    'question-url': row.key,
                    'date': 'xpath:./ancestor::table//tr[contains(th/text(), "Posėdžio data")]/td/text()',
                    'status': 'xpath:./ancestor::table//tr[contains(th/text(), "Būsena")]/td/text()',
                })
            ])

    with bot.pipe('attachment preview links'):
        with bot.pipe('attachment preview').download(update={'source': row.value}):
            key = call(clean_redirect_url, 'xpath:/html/head/meta[@http-equiv="refresh"]/@content?')
            with bot.pipe('attachment preview links').select([(key, row.value['source'])]):
                bot.pipe('attachment preview').download(update={'source': row.value})

    with bot.pipe('attachment links'):
        bot.pipe('attachments').download(update={
            'question-url': row.value['question-url'],
            'date': row.value['date'],
            'status': row.value['status'],
        })

    bot.pipe('attachment preview').export('data/vilnius/vtaryba/attachment-previews.csv', include=['key', 'size', 'source'], update={
        'size': row.value['content'].length,
    })

    bot.pipe('attachments').export('data/vilnius/vtaryba/attachments.csv', update=attachment_export)

    bot.compact()


if __name__ == '__main__':
    botlib.runbot(define, run)
