"""pytest fixtures: one Chrome window for staff and a separate incognito window for the guest."""
import os
from pathlib import Path

import pytest
from selenium import webdriver

from pages.base import Page

try:  # read G02_STAFF_USER / G02_STAFF_PASSWORD from a local .env file if there is one
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

SCREENSHOTS = Path(__file__).parent / "screenshots"


def _chrome(incognito):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--window-size=1440,1000")
    opts.add_argument("--lang=en-US")
    # The shop runs on plain http://. Newer Chrome shows a full-page
    # "Connection is not secure" warning for http sites, which blocks the test,
    # so switch that warning off for the test browsers only.
    opts.add_argument(
        "--disable-features=HttpsUpgrades,HttpsFirstModeV2,HttpsFirstBalancedMode,"
        "HttpsFirstBalancedModeAutoEnable,HttpsFirstModeIncognito,"
        "HttpsFirstModeV2ForTypicallySecureUsers,HttpsFirstModeV2ForEngagedSites"
    )
    opts.add_experimental_option("prefs", {"https_only_mode_enabled": False})
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})  # keep JavaScript errors
    if incognito:
        opts.add_argument("--incognito")
    if os.getenv("HEADLESS", "0") == "1":
        opts.add_argument("--headless=new")
    return webdriver.Chrome(options=opts)  # Selenium Manager downloads chromedriver by itself


@pytest.fixture
def staff(request):
    driver = _chrome(incognito=False)
    yield Page(driver, SCREENSHOTS / request.node.name, "staff")
    driver.quit()


@pytest.fixture
def customer(request):
    driver = _chrome(incognito=True)
    yield Page(driver, SCREENSHOTS / request.node.name, "customer")
    driver.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """When a test fails, save a screenshot of both windows to show where it stopped."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        for name in ("staff", "customer"):
            page = item.funcargs.get(name)
            if page:
                try:
                    page.shot("FAILED")
                except Exception:
                    pass