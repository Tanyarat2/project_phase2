"""Shared settings and a small wrapper around Selenium WebDriver.

Every wait in this project is an explicit wait (WebDriverWait).
The tests never pause for a fixed time (no time.sleep).
"""
import datetime
import os
import re
import sys
from pathlib import Path

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("SHOP_URL", "http://157.85.102.236/shop").rstrip("/")
ADMIN_URL = f"{BASE_URL}/wp-admin"
TIMEOUT = int(os.getenv("UI_TIMEOUT", "30"))
SELECT_ALL = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL


def make_run_id():
    """Date and time of this run, e.g. 20261116-153012.

    Seconds are included so two runs in the same minute still create different data.
    """
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def norm(text):
    """Collapse whitespace and unify the special spaces and minus signs WooCommerce prints."""
    text = (text or "").replace(" ", " ").replace("−", "-")
    return re.sub(r"\s+", " ", text).strip()


def step(number, message):
    """Print progress so a run shows which test-case step it is on."""
    print(f"  Step {number}: {message}", flush=True)


class Page:
    """One browser window (staff or customer) with waiting helpers."""

    def __init__(self, driver, shot_dir, role):
        self.d = driver
        self.role = role
        self.shot_dir = Path(shot_dir)
        self.wait = WebDriverWait(
            driver,
            TIMEOUT,
            ignored_exceptions=(NoSuchElementException, StaleElementReferenceException),
        )

    # ---------- navigation ----------
    def go(self, url):
        self.d.get(url)

    # ---------- finding elements ----------
    def _first_visible(self, by, locator):
        def check(d):
            for el in d.find_elements(by, locator):
                if el.is_displayed():
                    return el
            return False

        return self.wait.until(check, message=f"[{self.role}] nothing visible for {locator}")

    def find(self, css):
        """Wait for the first VISIBLE element matching a CSS selector."""
        return self._first_visible(By.CSS_SELECTOR, css)

    def find_x(self, xpath):
        """Wait for the first VISIBLE element matching an XPath."""
        return self._first_visible(By.XPATH, xpath)

    def present(self, css):
        """Wait for an element to exist in the page, visible or not (e.g. hidden <select>)."""
        return self.wait.until(
            lambda d: d.find_element(By.CSS_SELECTOR, css),
            message=f"[{self.role}] not in page: {css}",
        )

    def all(self, css):
        return self.d.find_elements(By.CSS_SELECTOR, css)

    # ---------- actions ----------
    def click(self, target):
        """Click a CSS selector or an element once it is clickable."""
        if isinstance(target, str):
            css = target

            def clickable(d):
                for el in d.find_elements(By.CSS_SELECTOR, css):
                    if el.is_displayed() and el.is_enabled():
                        return el
                return False

            el = self.wait.until(clickable, message=f"[{self.role}] not clickable: {css}")
        else:
            el = target
        self.d.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            el.click()
        except ElementClickInterceptedException:
            # A sticky header, admin notice or tour popup is covering the element.
            self.d.execute_script("arguments[0].click();", el)

    def js_click(self, el):
        """Click elements that are only shown on hover (e.g. WordPress row actions)."""
        self.d.execute_script("arguments[0].click();", el)

    def fill(self, target, value):
        """Replace the content of a text/number field (works with React fields too)."""
        el = self.find(target) if isinstance(target, str) else target
        value = str(value)
        self.d.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        el.send_keys(SELECT_ALL, "a")
        el.send_keys(Keys.DELETE)
        if (el.get_attribute("value") or "") != "":
            # Select-all did not catch (e.g. a field that starts with "0"): empty it another way.
            el.clear()
            if (el.get_attribute("value") or "") != "":
                self._set_value(el, "")
        if value != "":
            el.send_keys(value)
        if (el.get_attribute("value") or "") != value:
            self._set_value(el, value)  # last resort: set it directly and fire the input events
        return el

    def _set_value(self, el, value):
        self.d.execute_script(
            "const e = arguments[0], v = arguments[1];"
            "const proto = e.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;"
            "Object.getOwnPropertyDescriptor(proto, 'value').set.call(e, v);"
            "e.dispatchEvent(new Event('input', {bubbles: true}));"
            "e.dispatchEvent(new Event('change', {bubbles: true}));",
            el,
            value,
        )

    # ---------- reading ----------
    def body(self):
        return norm(self.d.find_element(By.TAG_NAME, "body").text)

    def wait_body(self, expected):
        """Wait until the visible page text contains `expected`."""
        self.wait.until(
            lambda d: expected in self.body(),
            message=f"[{self.role}] page never showed: {expected!r}",
        )

    def wait_text(self, css, expected, exact=False):
        """Wait until an element matching `css` shows `expected` (contains, or equals if exact)."""

        def check(d):
            for el in d.find_elements(By.CSS_SELECTOR, css):
                txt = norm(el.text)
                if (txt == expected) if exact else (expected in txt):
                    return el
            return False

        return self.wait.until(check, message=f"[{self.role}] {expected!r} not shown in {css}")

    def wait_notice(self, expected):
        """Wait for a WordPress admin notice such as 'Product published.'.

        WooCommerce moves admin notices into its own (sometimes collapsed) notice area,
        so this reads textContent, which works even when the notice is not visible.
        """
        css = "#message, .notice, .updated, .woocommerce-layout__notice-list"

        def check(d):
            for el in d.find_elements(By.CSS_SELECTOR, css):
                txt = norm(el.get_attribute("textContent"))
                if expected in txt:
                    return txt
            return False

        return self.wait.until(check, message=f"[{self.role}] admin notice {expected!r} not found")

    def validity(self, el):
        """The browser's own form validation state for an <input>."""
        return self.d.execute_script(
            "const e = arguments[0];"
            "return {message: e.validationMessage, valid: e.validity.valid,"
            " overflow: e.validity.rangeOverflow, underflow: e.validity.rangeUnderflow,"
            " typeMismatch: e.validity.typeMismatch};",
            el,
        )

    # ---------- evidence ----------
    def shot(self, name):
        """Save a screenshot as screenshots/<test>/<name>-<staff|customer>.png."""
        self.shot_dir.mkdir(parents=True, exist_ok=True)
        self.d.save_screenshot(str(self.shot_dir / f"{name}-{self.role}.png"))