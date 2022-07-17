from pages import BasePage, By, sleep

class GoogLoginPageLocators:
        EMAIL_INPUT = (By.XPATH, './/input[@type="email"]')
        GENERIC_NEXT_BUTTON = (By.XPATH, './/div[@data-primary-action-label]//button[@type="button"]/span')
        PASSWORD_INPUT = (By.XPATH, './/input[@type="password"]')
        AUTHORIZATION_ALLOW_BUTTON = (By.XPATH, './/button/span[contains(text(), "Allow")]')
        AUTHORIZATION_CANCEL_BUTTON = (By.XPATH, './/button/span[contains(text(), "Cancel")]')

class GoogLoginPage(BasePage):
    load_identifier = GoogLoginPageLocators.EMAIL_INPUT

    def __init__(self, driver, logger=None):
        super(GoogLoginPage, self).__init__(driver, logger)

    def login(self, email, password):
        self.log.info("Attempt to do login using : %s , %s" % (email, password))
        if self.wait_for_element(GoogLoginPageLocators.EMAIL_INPUT):
            self.set_text(GoogLoginPageLocators.EMAIL_INPUT, email)
        sleep(3)
        if self.wait_for_element(GoogLoginPageLocators.GENERIC_NEXT_BUTTON):
            self.click(GoogLoginPageLocators.GENERIC_NEXT_BUTTON)
        sleep(3)
        if self.wait_for_element(GoogLoginPageLocators.PASSWORD_INPUT):
            self.set_text(GoogLoginPageLocators.PASSWORD_INPUT, password)
        sleep(3)
        if self.wait_for_element(GoogLoginPageLocators.GENERIC_NEXT_BUTTON):
            self.click(GoogLoginPageLocators.GENERIC_NEXT_BUTTON)
        sleep(3)
        if (
                self.wait_for_element(GoogLoginPageLocators.AUTHORIZATION_CANCEL_BUTTON)
                or
                self.wait_for_element(GoogLoginPageLocators.AUTHORIZATION_ALLOW_BUTTON)
            ):
            self.click(GoogLoginPageLocators.GENERIC_NEXT_BUTTON)
        sleep(3)
        return True
