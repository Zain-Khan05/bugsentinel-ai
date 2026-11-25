"""Run against live local servers with RUN_SELENIUM=1 and APP_URL=http://localhost:3000."""
import os

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait


pytestmark = pytest.mark.skipif(os.getenv("RUN_SELENIUM") != "1", reason="Set RUN_SELENIUM=1 after starting frontend and backend")
APP_URL = os.getenv("APP_URL", "http://localhost:3000")
WAIT_SECONDS = 12


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1440,1000")
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(1)
    yield browser
    browser.quit()


def wait_for(driver, locator):
    return WebDriverWait(driver, WAIT_SECONDS).until(conditions.visibility_of_element_located(locator))


def login(driver):
    driver.get(APP_URL)
    email = wait_for(driver, (By.ID, "email"))
    email.clear()
    email.send_keys("developer@example.com")
    password = driver.find_element(By.ID, "password")
    password.clear()
    password.send_keys("ChangeMe123!")
    driver.find_element(By.XPATH, "//button[contains(., 'Enter workspace')]").click()
    wait_for(driver, (By.XPATH, "//h2[contains(., 'Review source code')]"))


def test_email_login_opens_dashboard(driver):
    login(driver)
    assert "Code intelligence" in driver.page_source


def test_invalid_login_displays_error(driver):
    driver.get(APP_URL)
    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys("developer@example.com")
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys("WrongPassword123")
    driver.find_element(By.XPATH, "//button[contains(., 'Enter workspace')]").click()
    error = wait_for(driver, (By.CSS_SELECTOR, ".error"))
    assert "Incorrect email or password" in error.text


def test_code_submission_displays_risk_report(driver):
    login(driver)
    source = driver.find_element(By.ID, "source")
    source.clear()
    source.send_keys('def read_config():\n    api_key = "demo-secret-value"\n    return api_key')
    driver.find_element(By.XPATH, "//button[contains(., 'Run analysis')]").click()
    report = wait_for(driver, (By.XPATH, "//*[contains(., 'OVERALL RISK SCORE')]"))
    assert "Why this score" in driver.page_source
    assert report.is_displayed()
    highlighted_code = driver.find_element(By.CSS_SELECTOR, "[data-testid='code-review']")
    assert highlighted_code.is_displayed()
    assert "Possible hard-coded secret" in highlighted_code.text


def test_logout_returns_to_login_screen(driver):
    login(driver)
    driver.find_element(By.XPATH, "//button[contains(., 'Sign out')]").click()
    assert wait_for(driver, (By.ID, "email")).is_displayed()
