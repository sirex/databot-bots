#!/usr/bin/env python3

import botlib

import selenium.common
import selenium.webdriver
import selenium.webdriver.support.ui
import selenium.webdriver.support.expected_conditions as ec

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class has_n_elements:
    def __init__(self, by, value, n):
        self.by = by
        self.value = value
        self.n = n

    def __call__(self, driver):
        return len(driver.find_elements(self.by, self.value)) == self.n


class Browser(selenium.webdriver.Chrome):

    def __init__(self):
        super().__init__('/usr/lib/chromium-browser/chromedriver')
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


def define(bot):
    bot.define('index urls')
    bot.define('index pages')


def run(bot):
    index_urls = bot.pipe('index urls')
    # index_urls.append(extract_index_urls())

    index_pages = bot.pipe('index pages')
    with index_urls:
        index_pages.download()


if __name__ == '__main__':
    botlib.runbot(define, run)
