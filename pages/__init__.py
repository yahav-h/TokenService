from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep, time


class BasePage:
    def __init__(self, driver):
        self._driver = driver
        self.load_identifier = None

    def get_current_url(self): return self._driver.current_url
    def get_source_page(self): return self._driver.page_source

    def login(self, email, password):
        pass

    def take_screenshot(self):
        self._driver.save_screenshot(f"{time()}.png")

    def get(self, url):
        self._driver.get(url)
        print('Navigating to URL : %s' % url)

    def cleanup(self):
        print('cleaning up chromedriver session')
        self._driver.delete_all_cookies()
        self._driver.quit()

    def wait_for_element(self, locator, timeout=5, retry=3):
        if retry == 0:
            return False
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.visibility_of_element_located(locator))
            print('element found in page')
            return True
        except:
            print('element %s was not found within %d [sec]' % (locator, timeout))
            retry -= 1
            return self.wait_for_element(locator, timeout, retry)

    def wait_for_element_to_be_clickable(self, locator, timeout=5):
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.element_to_be_clickable(locator))
            return True
        except Exception as e:
            print("Element %s was not clickable after: %d [sec]" % (locator[1], timeout))
            print(e)
            return False

    def click(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        clickable = self.wait_for_element_to_be_clickable(locator, timeout)
        if clickable:
            try:
                self.find_element(locator).click()
            except Exception as e:
                print("Cannot click Element %s " % locator[1])
                print(e)
                retry -= 1
                return self.click(locator, timeout, retry)
            return True
        else:
            print("Cannot click Element %s" % locator[1])
            retry -= 1
            return self.click(locator, timeout, retry)

    def get_elements(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        element_found = self.wait_for_element(locator, timeout)
        if element_found:
            by, loc = locator
            elems = self._driver.find_elements(by, loc)
            print('elements found by : %s ' % loc)
            return elems
        else:
            print("Element %s was not found after: %d [sec]" % (locator[1], timeout))
            retry -= 1
            return self.find_element(locator, timeout, retry)

    def find_element(self, locator, timeout=10, retry=6):
        if retry == 0:
            return
        element_found = self.wait_for_element(locator, timeout)
        if element_found:
            by, loc = locator
            elem = self._driver.find_element(by, loc)
            print('element found by : %s ' % loc)
            return elem
        else:
            print("Element %s was not found after: %d [sec]" % (locator[1], timeout))
            retry -= 1
            return self.find_element(locator, timeout, retry)

    def wait_for_page_to_load(self, timeout=10, retry=6):
        if retry == 0:
            return False
        print("Will Wait: %d [sec] for page to load" % timeout)
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(self.load_identifier))
            print('Page loaded completely')
            return True
        except:
            print('Page failed to load within %d [sec]' % timeout)
            retry -= 1
            return self.wait_for_page_to_load(timeout, retry)

    def set_text(self, locator, text, timeout=10, retry=6):
        if retry == 0:
            return False
        element_appear = self.wait_for_element(locator, timeout)
        if not element_appear:
            print("Element %s wasn't found after: 5 [sec]" % locator[1])
            retry -= 1
            return self.set_text(locator, text, timeout, retry)
        try:
            elem = self.find_element(locator, timeout)
            elem.clear()
            elem.send_keys(text)
        except Exception as e:
            print("Cant send keys: %s To Element %s" % (text, locator[1]))
            print(e)
            retry -= 1
            return self.set_text(locator, text, timeout, retry)
        print('Setting Text completed : %s -> %s' % (locator[1], text))
        return True
