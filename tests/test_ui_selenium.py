"""Run separately after `docker compose up`: RUN_SELENIUM=1 pytest tests/test_ui_selenium.py."""
import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

@pytest.mark.skipif(os.getenv("RUN_SELENIUM") != "1", reason="Set RUN_SELENIUM=1 with ChromeDriver available")
def test_dashboard_login():
    driver = webdriver.Chrome()
    try:
        driver.get(os.getenv("APP_URL", "https://localhost"))
        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys("developer@example.com")
        driver.find_element(By.ID, "password").send_keys("ChangeMe123!")
        driver.find_element(By.TAG_NAME, "button").click()
        assert "New source scan" in driver.page_source
    finally:
        driver.quit()
