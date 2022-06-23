from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep


class MSOLoginPageLocators:
    INPUT_USERNAME = (By.XPATH, '//input[@type="email"]')
    INPUT_PASSWORD = (By.XPATH, '//input[@name="passwd"]')
    BTN_NEXT = (By.XPATH, '//input[@type="submit"]')


class MSOLoginPage:
    _driver = None
    log = None

    def __init__(self, driver, logger=None):
        self.log = logger
        self._driver = driver
        self.load_identifier = MSOLoginPageLocators.INPUT_USERNAME

    def login(self, email, password):
        self.log.info("Attempt to do login using : " + email + " , " + password)
        if not self.wait_for_element(MSOLoginPageLocators.INPUT_USERNAME):
            return False
        if not self.set_text(MSOLoginPageLocators.INPUT_USERNAME, email):
            return False
        sleep(3)
        if not self.wait_for_element(MSOLoginPageLocators.INPUT_PASSWORD):
            return False
        if not self.set_text(MSOLoginPageLocators.INPUT_PASSWORD, password):
            return False
        sleep(3)
        if not self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
            return False
        if not self.click(MSOLoginPageLocators.BTN_NEXT):
            return False
        sleep(3)
        if not self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
            return False
        if not self.click(MSOLoginPageLocators.BTN_NEXT):
            return False
        sleep(3)
        if not self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
            return False
        if not self.click(MSOLoginPageLocators.BTN_NEXT):
            return False
        return True

    def get(self, url):
        self._driver.get(url)

    def cleanup(self):
        self._driver.delete_all_cookies()
        self._driver.quit()

    def wait_for_element(self, locator, timeout=5):
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(locator))
            return True
        except:
            return False

    def wait_for_element_to_be_clickable(self, locator, timeout=5):
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.element_to_be_clickable(locator))
            return True
        except Exception as e:
            self.log.info("Element " + locator[1] + "wasnt clickable after: " + str(timeout) + " [sec]")
            self.log.error(e)
            return False

    def click(self, locator, timeout=5):
        clickable = self.wait_for_element_to_be_clickable(locator, timeout)
        if clickable:
            try:
                self.find_element(locator).click()
            except Exception as e:
                self.log.info("Cannot click Element " + locator[1])
                self.log.error(e)
                return False
            return True
        else:
            print("Cannot click Element " + locator[1])
            return False

    def find_element(self, locator, timeout=5):
        element_found = self.wait_for_element(locator, timeout)
        if element_found:
            return self._driver.find_element(locator[0], locator[1])
        else:
            self.log.info("Element" + locator[1] + " wasn't found after: " + str(timeout) + " [sec]")
            return None

    def wait_for_page_to_load(self, timeout=5, screenshot=False):
        self.log.info("Will Wait: " + str(timeout) + " [sec] for page to load")
        wait = WebDriverWait(self._driver, timeout)
        try:
            wait.until(EC.presence_of_element_located(self.load_identifier))
            return True
        except:
            return False

    def set_text(self, locator, text):
        element_appear = self.wait_for_element(locator)
        if not element_appear:
            self.log.info("Element" + locator[1] + " wasn't found after: 5 [sec]")
            return False
        try:
            self.find_element(locator).clear()
            self.find_element(locator).send_keys(text)
        except Exception as e:
            self.log.info("Cant send keys:" + text + "To Element" + locator[1] + " : " + str(e))
            self.log.error(e)
            return False
        return True
