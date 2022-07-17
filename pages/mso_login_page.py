from pages import BasePage, By, sleep


class MSOLoginPageLocators:
    INPUT_USERNAME = (By.XPATH, '//input[@type="email"]')
    INPUT_PASSWORD = (By.XPATH, '//input[@name="passwd"]')
    BTN_NEXT = (By.XPATH, '//input[@type="submit"]')


class MSOLoginPage(BasePage):
    load_identifier = MSOLoginPageLocators.INPUT_USERNAME

    def __init__(self, driver, logger=None):
        super(MSOLoginPage, self).__init__(driver, logger)

    def login(self, email, password):
        self.log.info("Attempt to do login using : %s , %s" % (email, password))
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
        return True
