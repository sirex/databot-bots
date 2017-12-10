#!/usr/bin/env python3

import botlib

from databot import define, task, this, strformat


search_url = 'https://www.limis.lt/greita-paieska/rezultatai/-/exhibitList/form?searchOnlySimpleMetadata=false&searchOnlyWithImages=false&searchInExhibits=true&searchInArchives=true&searchInLibraries=true&searchInAudioVideo=true&searchInPhotos=true&s_tab=&s_id=2duvdg1N5K4dHB0W&backUrl=https%3a%2f%2fwww.limis.lt%2fpradinis%2f-%2fexhibitSearchFast%2fform&listDisplayMode=simple&_exhibitListportlet_WAR_limiskportlet_searchType=&page={page}&rowsOnPage=48'

pipeline = {
    'pipes': [
        define('paieška'),
        define('paieškos-puslapių-numeriai'),
        define('paieškos-puslapiai', compress=True),
        define('eksponatų-nuorodos'),
        define('eksponatų-puslapiai', compress=True),
    ],
    'tasks': [
        task('paieška').daily().clean().download(search_url.format(page=1), check='select[name=page]'),

        task('paieška', 'paieškos-puslapių-numeriai').daily().
        select(['select[name=page] option @value']).
        dedup(),

        task('paieškos-puslapių-numeriai', 'paieškos-puslapiai').
        download(strformat(search_url, page=this.key), check='#exhibitListBlockId'),

        task('paieškos-puslapiai', 'eksponatų-nuorodos').select([
            '#exhibitListBlockId .thumbs-with-title > li span.vertical-scroller > a', ('@href', ':text'),
        ]),

        task('eksponatų-nuorodos', 'eksponatų-puslapiai').download(check='#exhibit_block_main_info'),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
