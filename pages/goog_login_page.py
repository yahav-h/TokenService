from pages import BasePage, By, sleep

class GoogLoginPageLocators:
        EMAIL_INPUT = (By.XPATH, './/input[@type="email"]')
        GENERIC_NEXT_BUTTON = (By.XPATH, './/div[@data-primary-action-label]//button[@type="button"]/span')
        PASSWORD_INPUT = (By.XPATH, './/input[@type="password"]')
        AUTHORIZATION_CONTINUE_BUTTON = (By.XPATH, './/button/span[contains(text(), "Continue")]')
        AUTHORIZATION_ALLOW_BUTTON = (By.XPATH, './/button/span[contains(text(), "Allow")]')
        GENERIC_ACCESS_CHECKBOXES = (By.XPATH, './/input[@type="checkbox"]')

class GoogLoginPage(BasePage):
    def __init__(self, driver, logger=None):
        super(GoogLoginPage, self).__init__(driver, logger)
        self.load_identifier = GoogLoginPageLocators.EMAIL_INPUT

    def login(self, user, password):
        try:

            if self.wait_for_element(GoogLoginPageLocators.EMAIL_INPUT):
                self.set_text(GoogLoginPageLocators.EMAIL_INPUT, user)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.GENERIC_NEXT_BUTTON):
                self.click(GoogLoginPageLocators.GENERIC_NEXT_BUTTON)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.PASSWORD_INPUT):
                self.set_text(GoogLoginPageLocators.PASSWORD_INPUT, password)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.GENERIC_NEXT_BUTTON):
                self.click(GoogLoginPageLocators.GENERIC_NEXT_BUTTON)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.AUTHORIZATION_CONTINUE_BUTTON):
                self.click(GoogLoginPageLocators.AUTHORIZATION_CONTINUE_BUTTON)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.GENERIC_ACCESS_CHECKBOXES):
                for elem in self.get_elements(GoogLoginPageLocators.GENERIC_ACCESS_CHECKBOXES):
                    elem.click()
                    sleep(5)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.AUTHORIZATION_CONTINUE_BUTTON):
                self.click(GoogLoginPageLocators.AUTHORIZATION_CONTINUE_BUTTON)
            sleep(5)

            if self.wait_for_element(GoogLoginPageLocators.AUTHORIZATION_ALLOW_BUTTON):
                self.click(GoogLoginPageLocators.AUTHORIZATION_ALLOW_BUTTON)
            sleep(5)
        except Exception as e:
            print(e)
        url = self._driver.current_url
        return url
