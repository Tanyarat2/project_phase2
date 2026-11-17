"""Guest-customer actions on the storefront (block theme, block Cart and block Checkout)."""
import re
from urllib.parse import quote_plus

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base import BASE_URL, norm

CART_TOTAL = ".wc-block-components-totals-footer-item .wc-block-components-totals-item__value"
DISCOUNT = ".wc-block-components-totals-discount .wc-block-components-totals-item__value"
COUPON_INPUT = "#wc-block-components-totals-coupon__input-coupon"
COUPON_ERROR = "#validate-error-coupon"
ADDED_NOTICE = ".wc-block-components-notice-banner.is-success, .woocommerce-message"
COD_RADIO = "#radio-control-wc-payment-method-options-cod"
QTY_INPUT = "//input[contains(@class,'wc-block-components-quantity-selector__input')]"
CITY_ERROR = (
    "//input[@id='billing-city']/ancestor::div[contains(@class,'wc-block-components-text-input')][1]"
    "//*[contains(@class,'wc-block-components-validation-error')]"
)


def _card_xpath(name):
    """A product card in a product list (shop, category or search results)."""
    return (
        "//li[contains(concat(' ', normalize-space(@class), ' '), ' product ')]"
        f"[.//a[normalize-space()='{name}']]"
    )


def _row_xpath(name):
    """A product line in the block Cart."""
    return (
        "//tr[contains(@class,'wc-block-cart-items__row')]"
        f"[.//a[contains(@class,'wc-block-components-product-name') and normalize-space()='{name}']]"
    )


# ---------------------------------------------------------------- browsing
def open_home(p):
    p.go(f"{BASE_URL}/")
    p.find("li.wc-block-product, li.product")
    return {
        "product_cards": len(p.all("li.wc-block-product, li.product")),
        "logged_in": bool(p.all("#wpadminbar")),
    }


def cart_count(p):
    """Number shown by the mini-cart icon in the header."""
    buttons = p.all("button.wc-block-mini-cart__button")
    m = re.search(r"(\d+)", buttons[0].get_attribute("aria-label") or "") if buttons else None
    return int(m.group(1)) if m else None


def wait_cart_count(p, n):
    p.wait.until(lambda d: cart_count(p) == n, message=f"cart count never became {n}")


def search_product(p, name):
    """Search the shop. WooCommerce jumps straight to the product page when only one matches."""
    p.go(f"{BASE_URL}/?s={quote_plus(name)}&post_type=product")
    p.wait.until(
        lambda d: "/product/" in d.current_url or d.find_elements(By.XPATH, _card_xpath(name)),
        message=f"search did not find {name}",
    )
    if "/product/" in p.d.current_url:
        return product_page_info(p)
    card = p.find_x(_card_xpath(name))
    price = card.find_element(By.CSS_SELECTOR, ".wc-block-components-product-price, .price")
    return {"name": name, "price": norm(price.text)}


def open_category(p, slug, label):
    """Open a category from the shop page (falls back to its URL if no link is visible)."""
    links = [a for a in p.all(f"a[href*='/product-category/{slug}']") if a.is_displayed()]
    if links:
        p.click(links[0])
    else:
        p.go(f"{BASE_URL}/product-category/{slug}/")
    p.wait.until(lambda d: f"/product-category/{slug}" in d.current_url)
    p.wait.until(lambda d: label in d.title)
    p.find("li.wc-block-product, li.product")


def sort_by(p, value):
    """value: 'date' = Sort by latest."""
    Select(p.find("select.orderby")).select_by_value(value)
    p.wait.until(lambda d: f"orderby={value}" in d.current_url)


def list_names(p):
    return [
        norm(a.get_attribute("textContent"))
        for a in p.all("li.wc-block-product .wp-block-post-title a, li.product .woocommerce-loop-product__title")
    ]


def list_classes(p):
    return [li.get_attribute("class") for li in p.all("li.wc-block-product, li.product")]


def card_price(p, name):
    card = p.find_x(_card_xpath(name))
    return norm(card.find_element(By.CSS_SELECTOR, ".wc-block-components-product-price, .price").text)


def open_product_from_list(p, name):
    if "/product/" not in p.d.current_url:
        p.click(p.find_x(_card_xpath(name) + f"//a[normalize-space()='{name}']"))
    return product_page_info(p)


def product_page_info(p):
    p.find("form.cart")
    return {
        "name": norm(p.find("h1").text),
        "price": norm(p.find(".wc-block-components-product-price, p.price").text),
        "body": p.body(),
    }


def add_to_cart(p, qty):
    """Type a quantity on the product page and click Add to cart. Returns the quantity field."""
    qty_input = p.fill("form.cart input.qty", qty)
    p.click("form.cart button.single_add_to_cart_button")
    return qty_input


def wait_added_notice(p):
    return norm(p.wait_text(ADDED_NOTICE, "added to your cart").text)


# ---------------------------------------------------------------- cart
def open_cart(p):
    p.go(f"{BASE_URL}/cart/")
    p.find(".wc-block-cart-items__row")


def cart_line(p, name):
    row = p.find_x(_row_xpath(name))
    return {
        "lines": len(p.all(".wc-block-cart-items__row")),
        "qty": row.find_element(By.XPATH, "." + QTY_INPUT).get_attribute("value"),
        "line_total": norm(
            row.find_element(
                By.CSS_SELECTOR, ".wc-block-cart-item__total .wc-block-components-product-price__value"
            ).text
        ),
        "total": cart_total(p),
    }


def cart_total(p):
    return norm(p.find(CART_TOTAL).text)


def wait_total(p, amount):
    p.wait_text(CART_TOTAL, amount, exact=True)


def set_cart_qty(p, name, qty):
    """Type a quantity into the cart line, then leave the field (Tab)."""
    field = p.find_x(_row_xpath(name) + QTY_INPUT)
    p.fill(field, qty)
    try:
        field.send_keys(Keys.TAB)
    except StaleElementReferenceException:  # the cart re-drew the row while typing
        p.find_x(_row_xpath(name) + QTY_INPUT).send_keys(Keys.TAB)


def wait_cart_qty(p, name, qty):
    p.wait.until(
        lambda d: d.find_element(By.XPATH, _row_xpath(name) + QTY_INPUT).get_attribute("value") == str(qty),
        message=f"cart quantity never became {qty}",
    )


def wait_line_total(p, name, amount):
    xpath = (
        _row_xpath(name)
        + "//td[contains(@class,'wc-block-cart-item__total')]"
        + "//*[contains(@class,'wc-block-components-product-price__value')]"
    )
    p.wait.until(
        lambda d: norm(d.find_element(By.XPATH, xpath).text) == amount,
        message=f"line total never became {amount}",
    )


def open_coupon_form(p):
    toggle = p.find_x(
        "//*[contains(@class,'wc-block-components-panel__button')][contains(normalize-space(),'Add coupons')]"
    )
    if toggle.get_attribute("aria-expanded") != "true":
        p.click(toggle)
    return p.find(COUPON_INPUT)


def apply_coupon(p, code):
    p.fill(open_coupon_form(p), code)
    p.click("button.wc-block-components-totals-coupon__button")


def wait_coupon_error(p, contains):
    return norm(p.wait_text(COUPON_ERROR, contains).text)


def discount(p):
    found = [e for e in p.all(DISCOUNT) if e.is_displayed()]
    return norm(found[0].text) if found else None


def wait_discount(p, amount):
    return norm(p.wait_text(DISCOUNT, amount).text)


def applied_coupons(p):
    return " ".join(
        norm(e.get_attribute("textContent")) for e in p.all(".wc-block-components-totals-discount__coupon-list")
    ).lower()


def proceed_to_checkout(p):
    p.click("a.wc-block-cart__submit-button")
    p.find("#email")
    wait_checkout_loaded(p)


# ---------------------------------------------------------------- checkout
def wait_checkout_loaded(p):
    """The block Checkout first shows grey placeholder bars; wait for the real order summary."""
    p.present(".wc-block-components-order-summary-item__quantity")
    p.wait.until(
        lambda d: any(
            "฿" in norm(e.text) for e in d.find_elements(By.CSS_SELECTOR, CART_TOTAL) if e.is_displayed()
        ),
        message="checkout order summary never finished loading",
    )


def checkout_summary(p):
    wait_checkout_loaded(p)
    found = [
        i for i in p.all(".wc-block-components-order-summary-item")
        if i.find_elements(By.CSS_SELECTOR, ".wc-block-components-order-summary-item__quantity")
    ]
    shown = [i for i in found if i.is_displayed()] or found
    items = []
    for item in shown:
        names = item.find_elements(By.CSS_SELECTOR, ".wc-block-components-product-name")
        if not names:
            names = item.find_elements(By.CSS_SELECTOR, ".wc-block-components-order-summary-item__description")
        qty = item.find_element(
            By.CSS_SELECTOR, ".wc-block-components-order-summary-item__quantity span[aria-hidden='true']"
        )
        name = norm(names[0].get_attribute("textContent")) if names else ""
        items.append((name, norm(qty.get_attribute("textContent"))))
    return {
        "items": list(dict.fromkeys(items)),  # the summary can be rendered twice (desktop + mobile)
        "discount": discount(p),
        "total": cart_total(p),
        "cod_available": bool(p.all(COD_RADIO)),
    }


def select_cod(p):
    if not p.present(COD_RADIO).is_selected():
        p.click(p.find(f"label[for='{COD_RADIO[1:]}']"))
    return p.present(COD_RADIO).is_selected()


def fill_checkout(p, b, city=None):
    """Fill the billing form. Pass city='' to leave Town / City empty."""
    p.fill("#email", b["email"])
    Select(p.find("#billing-country")).select_by_value(b["country"])
    p.fill("#billing-first_name", b["first"])
    p.fill("#billing-last_name", b["last"])
    p.fill("#billing-address_1", b["address"])
    p.fill("#billing-city", b["city"] if city is None else city)
    Select(p.find("#billing-state")).select_by_value(b["state"])
    p.fill("#billing-postcode", b["postcode"])
    p.fill("#billing-phone", b["phone"])
    return select_cod(p)


def field_errors(p):
    return [norm(e.text) for e in p.all(".wc-block-components-validation-error") if e.is_displayed()]


def place_order(p):
    p.click(".wc-block-components-checkout-place-order-button")


def wait_city_error(p):
    return norm(p.find_x(CITY_ERROR).text)


def wait_order_received(p):
    """Wait for the Order received page and return the order number from its URL."""
    WebDriverWait(p.d, 90).until(EC.url_contains("/order-received/"))
    p.wait_body("Thank you. Your order has been received.")
    return int(re.search(r"/order-received/(\d+)", p.d.current_url).group(1))


# ---------------------------------------------------------------- reviews
def open_reviews_tab(p):
    tab = p.find("a[href='#tab-reviews']")
    panels = p.all("#tab-reviews")
    if not panels or not panels[0].is_displayed():
        p.click(tab)
    p.find("#tab-reviews")
    return reviews_tab_title(p)


def reviews_tab_title(p):
    return norm(p.present("a[href='#tab-reviews']").get_attribute("textContent"))


def fill_review(p, rating, text, name, email):
    if rating:
        p.click(f"p.stars a.star-{rating}")
    p.fill("#comment", text)
    p.fill("#author", name)
    p.fill("#email", email)


def selected_rating(p):
    return p.present("#rating").get_attribute("value")


def submit_review(p):
    p.click("#submit")


def review_item(p, text):
    li = p.find_x(f"//*[@id='reviews']//li[contains(@class,'review')][.//*[contains(normalize-space(), '{text}')]]")
    author = li.find_elements(By.CSS_SELECTOR, ".woocommerce-review__author")
    stars = li.find_elements(By.CSS_SELECTOR, ".star-rating")
    awaiting = li.find_elements(By.CSS_SELECTOR, ".woocommerce-review__awaiting-approval")
    return {
        "text": norm(li.text),
        "author": norm(author[0].text) if author else "",
        "rating": (stars[0].get_attribute("aria-label") or "") if stars else "",
        "awaiting": norm(awaiting[0].text) if awaiting else "",
    }