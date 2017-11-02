#!/usr/bin/env python3

import botlib

import selenium.common
import selenium.webdriver
import selenium.webdriver.support.ui
import selenium.webdriver.support.expected_conditions as ec

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException

from databot import define, task


class has_n_elements:
    def __init__(self, by, value, n):
        self.by = by
        self.value = value
        self.n = n

    def __call__(self, driver):
        return len(driver.find_elements(self.by, self.value)) == self.n


class attribute_has_changed:
    def __init__(self, by, selector, attribute, value):
        self.by = by
        self.selector = selector
        self.attribute = attribute
        self.value = value

    def __call__(self, driver):
        try:
            elem = driver.find_element(self.by, self.selector)
            value = elem.get_attribute(self.attribute)
        except StaleElementReferenceException:
            return False
        else:
            return self.value != value


class Browser(selenium.webdriver.Chrome):

    def __init__(self):
        options = selenium.webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        super().__init__(chrome_options=options)
        self.wait = WebDriverWait(self, 10)
        self.set_page_load_timeout(10)

    def wait_element_by_class_name(self, name):
        return self.wait.until(ec.visibility_of_element_located((By.CLASS_NAME, name)))

    def wait_element_by_xpath(self, xpath):
        return self.wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))

    def wait_n_elemens_by_css_selector(self, n, selector):
        return self.wait.until(has_n_elements(By.CSS_SELECTOR, selector, n))


def extract_index_urls():
    browser = Browser()

    try:
        # Search for metrics
        browser.get('http://www.epaveldas.lt/patikslintoji-paieska')

        browser.wait_element_by_xpath('//button[@value="Ieškoti"]')
        browser.find_element_by_xpath('//label[text()="tekstas"]/preceding-sibling::input[1]').click()
        browser.wait_element_by_xpath('//label[text()="periodika"]')
        browser.find_element_by_xpath('//button[@value="Ieškoti"]').click()
        browser.wait_element_by_class_name('objectsDataTable')

        # Change number of results in page to be 50
        browser.find_element_by_xpath('//select[contains(@id, "SlctPageSize")]/option[@value="50"]').click()
        browser.wait_n_elemens_by_css_selector(50, '.wInfo .searchResultDescription a')

        # Collect all search result links
        page = 1
        while True:
            first_item_link = None
            for row in browser.find_elements_by_css_selector('table.objectsDataTable > tbody > tr'):
                key = row.find_element_by_css_selector('.searchResultDescription a').get_attribute('href')
                if first_item_link is None:
                    first_item_link = key
                yield key, {
                    'title': row.find_element_by_css_selector('.searchResultDescription a').text,
                    'source': {
                        'title': row.find_element_by_css_selector('.wSourceTitle a').get_attribute('href'),
                        'link': row.find_element_by_css_selector('.wSourceTitle a').text,
                    }
                }

            page += 1
            try:
                browser.find_element_by_xpath('//a[contains(@id, "objectsPaginatoridx%d")]' % page).click()
            except NoSuchElementException:
                browser.get_screenshot_as_file('/tmp/epaveldas_done.png')
                break

            try:
                browser.wait.until(attribute_has_changed(By.CSS_SELECTOR, '.searchResultDescription a', 'href', first_item_link))
            except TimeoutException:
                browser.get_screenshot_as_file('/tmp/epaveldas_attribute_has_changed.png')

    except:
        browser.get_screenshot_as_file('/tmp/epaveldas_error.png')
        raise
    finally:
        browser.quit()


pipeline = {
    'pipes': [
        define('paieškos-nuorodos'),
    ],
    'tasks': [
        task('paieškos-nuorodos').once().clean().append(extract_index_urls(), progress='paieškos-nuorodos').dedup(),
    ],
}


if __name__ == '__main__':
    botlib.runbot(pipeline)
