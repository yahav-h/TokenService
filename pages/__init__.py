from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep


class BasePage:
    def __init__(self, driver, logger=None):
        self.log = logger
        self._driver = driver
        self.load_identifier = None

    def get_current_url(self): return self._driver.current_url
    def get_source_page(self): return self._driver.page_source

    def login(self, email, password):
        pass

    def get(self, url):
        self._driver.get(url)
        self.log.info('Navigating to URL : %s' % url)

    def cleanup(self):
        self.log.info('cleaning up chromedriver session')
        self._driver.delete_all_cookies()
        self._driver.quit()

    def wait_for_element(self, locator, timeout=10, retry=6):
        if retry == 0:
            return False
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.visibility_of_element_located(locator))
            self.log.info('element found in page')
            return True
        except:
            self.log.warning('element %s was not found within %d [sec]' % (locator, timeout))
            retry -= 1
            return self.wait_for_element(locator, timeout, retry)

    def wait_for_element_to_be_clickable(self, locator, timeout=5):
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.element_to_be_clickable(locator))
            return True
        except Exception as e:
            self.log.warining("Element %s was not clickable after: %d [sec]" % (locator[1], timeout))
            self.log.error(e)
            return False

    def click(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        clickable = self.wait_for_element_to_be_clickable(locator, timeout)
        if clickable:
            try:
                self.find_element(locator).click()
            except Exception as e:
                self.log.warning("Cannot click Element %s " % locator[1])
                self.log.error(e)
                retry -= 1
                return self.click(locator, timeout, retry)
            return True
        else:
            self.log.warning("Cannot click Element %s" % locator[1])
            retry -= 1
            return self.click(locator, timeout, retry)

    def get_elements(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        element_found = self.wait_for_element(locator, timeout)
        if element_found:
            by, loc = locator
            elems = self._driver.find_elements(by, loc)
            self.log.info('elements found by : %s ' % loc)
            return elems
        else:
            self.log.warning("Element %s was not found after: %d [sec]" % (locator[1], timeout))
            retry -= 1
            return self.find_element(locator, timeout, retry)

    def find_element(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        element_found = self.wait_for_element(locator, timeout)
        if element_found:
            by, loc = locator
            elem = self._driver.find_element(by, loc)
            self.log.info('element found by : %s ' % loc)
            return elem
        else:
            self.log.warning("Element %s was not found after: %d [sec]" % (locator[1], timeout))
            retry -= 1
            return self.find_element(locator, timeout, retry)

    def wait_for_page_to_load(self, timeout=10, retry=6):
        if retry == 0:
            return False
        self.log.info("Will Wait: %d [sec] for page to load" % timeout)
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(self.load_identifier))
            self.log.info('Page loaded completely')
            return True
        except:
            self.log.warning('Page failed to load within %d [sec]' % timeout)
            retry -= 1
            return self.wait_for_page_to_load(timeout, retry)

    def set_text(self, locator, text, timeout=10, retry=6):
        if retry == 0:
            return False
        element_appear = self.wait_for_element(locator, timeout)
        if not element_appear:
            self.log.warning("Element %s wasn't found after: 5 [sec]" % locator[1])
            retry -= 1
            return self.set_text(locator, text, timeout, retry)
        try:
            elem = self.find_element(locator, timeout)
            elem.clear()
            elem.send_keys(text)
        except Exception as e:
            self.log.warning("Cant send keys: %s To Element %s" % (text, locator[1]))
            self.log.error(e)
            retry -= 1
            return self.set_text(locator, text, timeout, retry)
        self.log.info('Setting Text completed : %s -> %s' % (locator[1], text))
        return True
