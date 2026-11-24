from selenium import webdriver

print("Starting Selenium automation...")

driver = webdriver.Chrome()

try:
    driver.get("https://www.google.com")
    print("Website title:", driver.title)
finally:
    driver.quit()

print("Selenium test completed!")
