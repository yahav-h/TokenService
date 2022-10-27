from pages import BasePage, By, sleep


class MSOLoginPageLocators:
    INPUT_USERNAME = (By.XPATH, '//input[@type="email"]')
    INPUT_PASSWORD = (By.XPATH, '//input[@name="passwd"]')
    BTN_NEXT = (By.XPATH, '//input[@type="submit"]')


class MSOLoginPage(BasePage):
    def __init__(self, driver):
        super(MSOLoginPage, self).__init__(driver)
        self.load_identifier = MSOLoginPageLocators.INPUT_USERNAME

    def login(self, email, password):
        try:
            print("Attempt to do login using : %s , %s" % (email, password))
            if self.wait_for_element(MSOLoginPageLocators.INPUT_USERNAME):
                self.set_text(MSOLoginPageLocators.INPUT_USERNAME, email)
            sleep(3)
            if self.wait_for_element(MSOLoginPageLocators.INPUT_PASSWORD):
                self.set_text(MSOLoginPageLocators.INPUT_PASSWORD, password)
            sleep(3)
            if self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
                self.click(MSOLoginPageLocators.BTN_NEXT)
            sleep(3)
            if not self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
                self.click(MSOLoginPageLocators.BTN_NEXT)
            sleep(3)
            if self.wait_for_element(MSOLoginPageLocators.BTN_NEXT):
                self.click(MSOLoginPageLocators.BTN_NEXT)
            sleep(3)
        except Exception as e:
            print(e)
        url = self._driver.current_url
        return url
