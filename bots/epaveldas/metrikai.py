#!/usr/bin/env python3

import re

from operator import itemgetter

import botlib

import selenium.common
import selenium.webdriver
import selenium.webdriver.support.ui
import selenium.webdriver.support.expected_conditions as ec

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from databot import define, task, select, this


class has_n_elements:
    def __init__(self, by, value, n):
        self.by = by
        self.value = value
        self.n = n

    def __call__(self, driver):
        return len(driver.find_elements(self.by, self.value)) == self.n


class Browser(selenium.webdriver.Firefox):

    def __init__(self):
        super().__init__()
        self.wait = WebDriverWait(self, 10)
        self.set_page_load_timeout(10)

    def wait_element_by_class_name(self, name):
        return self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, name)))

    def wait_n_elemens_by_css_selector(self, n, selector):
        return self.wait.until(has_n_elements(By.CSS_SELECTOR, selector, n))


def extract_index_urls():
    browser = Browser()

    # Search for metrics
    browser.get('http://www.epaveldas.lt/patikslintoji-paieska')
    browser.find_element_by_class_name('inputParam').send_keys('RKB metrikų knyga')
    browser.find_element_by_class_name('btn2Parts').click()
    browser.wait_element_by_class_name('objectsDataTable')

    # Change number of results in page to be 50
    browser.find_element_by_xpath('//select[contains(@id, "SlctPageSize")]/option[@value="50"]').click()
    browser.wait_n_elemens_by_css_selector(50, '.wInfo .searchResultDescription a')

    # Collect all search result links
    next_btn = browser.find_element_by_xpath('//img[@title="Sekantis psl."]/..')
    next_btn_style = next_btn.get_attribute('style')
    while 'cursor:default' not in next_btn_style:
        for link in browser.find_elements_by_css_selector('.wInfo .searchResultDescription a'):
            yield link.get_attribute('href'), link.text

        next_btn.click()

        try:
            browser.wait.until(ec.staleness_of(link))
        except TimeoutException:
            break

        next_btn = browser.find_element_by_xpath('//img[@title="Sekantis psl."]/..')
        next_btn_style = next_btn.get_attribute('style')

    browser.quit()


def merge_intervals(intervals):
    if intervals:
        intervals = iter(sorted(intervals, key=itemgetter(0)))
        low, high = next(intervals)
        for a, b in intervals:
            if a <= high:
                high = max(high, b)
            else:
                yield low, high
                low, high = a, b
        yield low, high


def parse_title(title):
    parapija, tail = title.split(' RKB ', 1)
    years = []
    for start, _, _, end in re.findall(r'(\d{4})((--|-|–)(\d{4}))? m\.', tail):
        start = int(start)
        end = int(end) if end else start
        years.append((start, end))
    if years:
        years = list(merge_intervals(years))
        start, end = zip(*years)
        start = min(start)
        end = max(end)
        total = sum(b - a for a, b in years)
    else:
        start = end = 0
    return {
        'parapija': parapija,
        'pradžia': start,
        'pabaiga': end,
        'trukmė': total,
    }


pipeline = {
    'pipes': [
        define('paieškos-nuorodos'),
        define('paieškos-puslapiai', compress=True),
        define('knygos-duomenys'),
    ],
    'tasks': [
        # task('paieškos-nuorodos').once().append(extract_index_urls(),
        #                                         progress='paieškos-nuorodos').dedup(),
        task('paieškos-nuorodos', 'paieškos-puslapiai').download(),
        task('paieškos-puslapiai', 'knygos-duomenys').select(this.key, {
            'url': this.value.url,
            'antraštė': select('.authorTitle').text(),
            'd1': select([
                '.entryTable tr', (
                    select('th:content'),
                    select('td:content').strip(),
                ),
            ]).apply(dict),
            'd2': select('.authorTitle').text().apply(parse_title),
        }),
        task('knygos-duomenys').export('data/epaveldas/metrikai/knygos.csv', update=lambda row: {
            'url': row.value['url'],
            'antraštė': row.value['antraštė'],
            'apimtis': row.value['d1']['Apimtis'],
            'kalbos': row.value['d1']['Kalbos'],
            'autoriai': row.value['d1'].get('Kolektyviai autoriai'),
            'parapija': row.value['d2']['parapija'],
            'pradžia': row.value['d2']['pradžia'],
            'pabaiga': row.value['d2']['pabaiga'],
            'trukmė': row.value['d2']['trukmė'],
        }),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
