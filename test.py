from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config import BROSWER_TYPE

def open_browser_with_options(url, browser):
    options = Options()
    options.add_experimental_option("detach", True)

    if browser == "chrome":
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
    else:
        raise ValueError("Browser type not supported")

    driver.get(url)

# Variables
url = "https://www.zhipin.com/web/geek/job-recommend?ka=header-job-recommend"
browser_type = BROSWER_TYPE

# Test case
open_browser_with_options(url, browser_type)
