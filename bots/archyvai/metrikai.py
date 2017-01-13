#!/usr/bin/env python3

import uuid

import tqdm
import botlib

from databot import call, task, select

import selenium.common
import selenium.webdriver
import selenium.webdriver.support.ui
import selenium.webdriver.support.expected_conditions as ec

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


class Browser(selenium.webdriver.Chrome):

    def __init__(self):
        super().__init__('/usr/lib/chromium-browser/chromedriver')
        self.wait = WebDriverWait(self, 10)
        self.set_page_load_timeout(10)

    def wait_element_by_class_name(self, name):
        return self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, name)))

    def wait_element_by_xpath(self, xpath):
        return self.wait.until(ec.presence_of_element_located((By.XPATH, xpath)))

    def wait_text_by_class_name(self, name, text):
        return self.wait.until(ec.text_to_be_present_in_element((By.CLASS_NAME, name), text))


def set_text(elem, text):
    elem.send_keys(Keys.CONTROL + 'a')
    elem.send_keys(Keys.DELETE)
    elem.send_keys(text)


def extract_archive_pages(years):
    browser = Browser()

    browser.get('https://eais-pub.archyvai.lt/eais/')
    browser.add_cookie({
        'name': 'JSESSIONID',
        'value': '',
        'path': '/eais',
    })

    browser.get('http://eais-pub.archyvai.lt/eais/faces/pages/forms/search/F3001.jspx')

    for year in tqdm.tqdm(years):
        set_text(browser.find_element_by_class_name('af_inputText_content'), 'RKB metrikų knyga')
        set_text(browser.find_elements_by_class_name('af_inputDate_content')[0], '%d-01-01' % year)
        set_text(browser.find_elements_by_class_name('af_inputDate_content')[1], '%d-01-01' % (year + 1))
        browser.find_element_by_class_name('af_commandButton').click()
        browser.wait_element_by_xpath('//table[contains(@id, "resultTreeTable")]')

        pages = browser.find_elements_by_xpath(
            '//select[contains(@id, "pageSelection")]/option'
        )

        for i in range(len(pages)):
            browser.find_element_by_xpath('//select[contains(@id, "pageSelection")]/option[@value="%s"]' % i).click()
            browser.wait_element_by_xpath('//table[contains(@id, "resultTreeTable")]')

            results = browser.find_elements_by_xpath(
                '//table[contains(@id, "resultTreeTable")]'
                '//a[contains(@class, "text_bold_true")]'
            )

            for j in range(len(results)):
                elements = browser.find_elements_by_xpath(
                    '//table[contains(@id, "resultTreeTable")]'
                    '//a[contains(@class, "text_bold_true")]'
                )
                elements[j].click()
                browser.wait_text_by_class_name('pageTitleInner', 'aprašas')

                yield str(uuid.uuid4()), {
                    'headers': {},
                    'cookies': {},
                    'status_code': 200,
                    'encoding': 'utf-8',
                    'content': browser.page_source.encode('utf-8'),
                }

                browser.find_element_by_class_name('af_commandButton').click()
                browser.wait_element_by_xpath('//table[contains(@id, "resultTreeTable")]')

    browser.quit()


def define(bot):
    bot.define('index pages')
    bot.define('data')


def run(bot):
    pages = bot.pipe('index pages')
    data = bot.pipe('data')

    # years = range(1812, 1921, 5)
    # pages.append(extract_archive_pages(years))

    with pages:
        data.clean().reset().select('.inventoryLabel:text', {
            'fondas': '.upperHierarchyTreeInner xpath:a[1]/text()',
            'apyrašas': '.upperHierarchyTreeInner xpath:a[2]/text()',
            'data': call(dict, [
                '.inventoryBaseDataTable tr', (
                    'td[1]:content',
                    'td[2]:content',
                )
            ]),
        })


pipeline = {
    'pipes': [
        define('index pages'),
        define('data'),
    ],
    'tasks': [
        task('index pages').call(extract_archive_pages, range(1812, 1921, 5)).clean().reset(),
        task('index pages', 'data').select('.inventoryLabel:text', {
            'fondas': '.upperHierarchyTreeInner xpath:a[1]/text()',
            'apyrašas': '.upperHierarchyTreeInner xpath:a[2]/text()',
            'data': select([
                '.inventoryBaseDataTable tr', (
                    'td[1]:content',
                    'td[2]:content',
                )
            ]).cast(dict),
        }),
    ],
}


if __name__ == '__main__':
    botlib.runbot(define, run)
