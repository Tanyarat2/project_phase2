"""Staff-side actions in WordPress Admin (WooCommerce)."""
import os
import re

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base import ADMIN_URL, norm

ORDER_STATUS_VALUES = {
    "Processing": "wc-processing",
    "Completed": "wc-completed",
    "Cancelled": "wc-cancelled",
}


def _go_menu_link(p, css, fallback_url):
    """Open an admin menu page by its link (works even when that submenu is collapsed)."""
    links = p.all(css)
    p.go(links[0].get_attribute("href") if links else fallback_url)


# ---------------------------------------------------------------- login
def login(p):
    user = os.getenv("G02_STAFF_USER")
    password = os.getenv("G02_STAFF_PASSWORD")
    assert user and password, "Set G02_STAFF_USER and G02_STAFF_PASSWORD first (see README.md)."
    p.go(f"{ADMIN_URL}/")
    p.shot("step01a-login-page")  # shows what the browser really opened
    u = p.find("#user_login")
    u.clear()
    u.send_keys(user)
    pw = p.find("#user_pass")
    pw.clear()
    pw.send_keys(password)
    p.click("#wp-submit")
    p.wait.until(
        lambda d: d.find_elements(By.CSS_SELECTOR, "#wpadminbar")
        or d.find_elements(By.CSS_SELECTOR, "#login_error")
    )
    errors = p.all("#login_error")
    assert not errors, f"Login failed: {norm(errors[0].text)}"
    p.find("#adminmenu")
    return {
        "in_admin": "/wp-admin" in p.d.current_url,
        "dashboard_menu": bool(p.all("#menu-dashboard")),
    }


# ---------------------------------------------------------------- products
def click_products_menu(p):
    """Click Products in the left menu and return the submenu labels."""
    p.click("#menu-posts-product > a")
    return norm(p.find("#menu-posts-product .wp-submenu").text)


def click_add_new_product(p):
    p.click("#menu-posts-product .wp-submenu a[href$='post-new.php?post_type=product']")
    p.find("#title")
    return {"title_field": True, "description_editor": bool(p.all("#postdivrich, #wp-content-wrap"))}


def fill_product(p, name, price, stock, category=None):
    """Fill the Add New Product form and return what the form now contains."""
    p.fill("#title", name)
    Select(p.find("#product-type")).select_by_value("simple")
    p.click("#woocommerce-product-data li.general_options a")
    p.fill("#_regular_price", price)
    p.click("#woocommerce-product-data li.inventory_options a")
    manage = p.find("#_manage_stock")
    if not manage.is_selected():
        p.click(manage)
    p.fill("#_stock", stock)
    cat_selected = None
    if category:
        box = p.find_x(
            f"//ul[@id='product_catchecklist']//label[normalize-space()='{category}']/input"
        )
        if not box.is_selected():
            p.click(box)
        cat_selected = box.is_selected()
    return {
        "type": p.present("#product-type").get_attribute("value"),
        "price": p.present("#_regular_price").get_attribute("value"),
        "manage_stock": p.present("#_manage_stock").is_selected(),
        "stock": p.present("#_stock").get_attribute("value"),
        "category_ticked": cat_selected,
    }


def click_publish(p):
    """Click the WordPress Publish button and wait for the page to reload.

    WordPress autosaves a draft as soon as the title is typed ("Saving Draft..."),
    and while that runs the Publish button has the class "disabled" and ignores clicks.
    So wait for the autosave to finish first, and click again if the page did not reload.
    (WordPress removes "&message=6" from the address right after loading, so the test
    waits for the old page to be replaced instead of looking at the address.)
    """
    for attempt in range(1, 4):
        p.wait.until(
            lambda d: "disabled" not in (d.find_element(By.ID, "publish").get_attribute("class") or ""),
            message="Publish button stayed disabled (autosave never finished)",
        )
        old_button = p.d.find_element(By.ID, "publish")
        p.click(old_button)
        try:
            WebDriverWait(p.d, 20).until(EC.staleness_of(old_button))  # the page reloaded
            p.present("#publish")
            return
        except TimeoutException:
            p.shot(f"publish-attempt{attempt}")
    raise AssertionError(
        "the page did not reload after clicking Publish 3 times.\n" + publish_diagnostics(p)
    )


def publish_diagnostics(p):
    """Explain why the WordPress edit form did not submit."""
    info = p.d.execute_script(
        """
        const form = document.getElementById('post');
        const invalid = form ? [...form.querySelectorAll(':invalid')]
            .map(e => (e.id || e.name || e.tagName) + ' -> ' + e.validationMessage) : ['no form#post'];
        const notices = [...document.querySelectorAll('.notice-error, .error, .woocommerce-error')]
            .map(e => e.innerText.trim().slice(0, 200)).filter(Boolean);
        const pub = document.getElementById('publish');
        return {
            url: location.href,
            invalid_fields: invalid,
            error_notices: notices,
            publish_button: pub ? pub.outerHTML.slice(0, 200) : 'missing',
            autosave: (document.querySelector('.autosave-message') || {}).textContent || '',
            login_popup: !!document.querySelector('#wp-auth-check-wrap:not(.hidden)'),
        };
        """
    )
    try:
        console = [e["message"][:300] for e in p.d.get_log("browser") if e["level"] == "SEVERE"][-8:]
    except Exception:
        console = ["(browser log not available)"]
    lines = [f"  {k}: {v}" for k, v in info.items()] + [f"  console errors: {console}"]
    return "\n".join(lines)


def publish_product(p):
    click_publish(p)
    return p.wait_notice("Product published.")


def find_product_row(p, name):
    """Products > All Products, search by name, return the list columns for that product."""
    _go_menu_link(
        p,
        "#menu-posts-product a[href$='edit.php?post_type=product']",
        f"{ADMIN_URL}/edit.php?post_type=product",
    )
    p.fill("#post-search-input", name)
    p.click("#search-submit")
    row = p.find_x(
        "//table[contains(@class,'wp-list-table')]//tbody/tr"
        f"[.//a[contains(@class,'row-title') and normalize-space()='{name}']]"
    )

    def cell(col):
        found = row.find_elements(By.CSS_SELECTOR, f"td.column-{col}")
        return norm(found[0].text) if found else ""

    return {
        "price": cell("price"),
        "stock": cell("is_in_stock"),
        "categories": cell("product_cat"),
    }


# ---------------------------------------------------------------- coupons
def open_add_new_coupon(p):
    """Marketing > Coupons > Add coupon."""
    _go_menu_link(
        p,
        "#toplevel_page_woocommerce-marketing a[href*='post_type=shop_coupon']",
        f"{ADMIN_URL}/edit.php?post_type=shop_coupon",
    )
    p.click("a.page-title-action[href*='post-new.php?post_type=shop_coupon']")
    p.find("#title")
    p.find("#discount_type")


def fill_coupon(p, code, discount_type, amount):
    p.fill("#title", code)
    Select(p.find("#discount_type")).select_by_value(discount_type)
    p.fill("#coupon_amount", amount)
    return {
        "code": p.present("#title").get_attribute("value"),
        "type": p.present("#discount_type").get_attribute("value"),
        "amount": p.present("#coupon_amount").get_attribute("value"),
    }


def publish_coupon(p):
    click_publish(p)
    message = p.wait_notice("Coupon updated.")
    status = norm(p.find("#post-status-display").text)
    return message, status


def find_coupon_row(p, code):
    _go_menu_link(
        p,
        "#toplevel_page_woocommerce-marketing a[href*='post_type=shop_coupon']",
        f"{ADMIN_URL}/edit.php?post_type=shop_coupon",
    )
    p.fill("#post-search-input", code)
    p.click("#search-submit")
    row = p.find_x(
        "//table[contains(@class,'wp-list-table')]//tbody/tr"
        f"[.//a[contains(@class,'row-title') and normalize-space()='{code}']]"
    )

    def cell(col):
        return norm(row.find_element(By.CSS_SELECTOR, f"td.column-{col}").text)

    return {"type": cell("type"), "amount": cell("amount"), "usage": cell("usage")}


# ---------------------------------------------------------------- orders
def open_orders(p):
    """WooCommerce > Orders (works with HPOS and with the older posts-based orders page)."""
    _go_menu_link(
        p,
        "#toplevel_page_woocommerce a[href*='page=wc-orders'],"
        " #toplevel_page_woocommerce a[href*='post_type=shop_order']",
        f"{ADMIN_URL}/admin.php?page=wc-orders",
    )
    return norm(p.wait_text(".wrap h1", "Orders").text)


def _order_row_xpath(order_id):
    return (
        "//table[contains(@class,'wp-list-table')]//tbody/tr"
        f"[.//a[contains(@class,'order-view') and starts-with(normalize-space(), '#{order_id} ')]]"
    )


def find_order_row(p, order_id):
    open_orders(p)
    p.fill("input[type='search'][name='s']", order_id)
    p.click("#search-submit")
    row = p.find_x(_order_row_xpath(order_id))
    status = row.find_elements(By.CSS_SELECTOR, "td.column-order_status")
    return {
        "row": row,
        "status": norm(status[0].text) if status else "",
        "text": norm(row.text),
    }


def order_details(p):
    """Read the order edit page."""
    p.find("#order_data")
    return {
        "status": p.present("#order_status").get_attribute("value"),
        "data": norm(p.find("#order_data").text),
        "items": norm(p.find("#woocommerce-order-items").text),
    }


def open_order(p, order_id):
    row = find_order_row(p, order_id)["row"]
    p.click(row.find_element(By.CSS_SELECTOR, "a.order-view"))
    return order_details(p)


def set_order_status(p, label):
    """Change the status drop-down and click Update. `label` is e.g. 'Completed'."""
    p.present("#order_status")
    # The status box is a select2 widget, so set the real <select> and fire its change event.
    p.d.execute_script(
        "jQuery('#order_status').val(arguments[0]).trigger('change');",
        ORDER_STATUS_VALUES[label],
    )
    p.click("button.save_order")
    message = p.wait_notice("Order updated.")
    return message, order_details(p)


# ---------------------------------------------------------------- reviews
def open_reviews(p):
    """Products > Reviews."""
    _go_menu_link(
        p,
        "#menu-posts-product a[href*='page=product-reviews']",
        f"{ADMIN_URL}/edit.php?post_type=product&page=product-reviews",
    )
    p.wait.until(lambda d: "page=product-reviews" in d.current_url)
    p.find(".subsubsub")
    p.present("#the-comment-list")
    p.wait_body("Reviews")
    return {"pending_link": bool(_status_links(p, "moderated"))}


STATUS_LABELS = {"moderated": "Pending", "approved": "Approved"}


def _status_links(p, status):
    """The 'Pending (n)' / 'Approved (n)' links above the reviews table."""
    label = STATUS_LABELS[status]
    return p.d.find_elements(
        By.XPATH,
        f"//ul[contains(@class,'subsubsub')]//a[contains(@href,'comment_status={status}')"
        f" or starts-with(normalize-space(), '{label}')]",
    )


def review_counts(p):
    def count(status):
        links = _status_links(p, status)
        m = re.search(r"\(([\d,]+)\)", norm(links[0].get_attribute("textContent"))) if links else None
        return int(m.group(1).replace(",", "")) if m else 0

    return {"pending": count("moderated"), "approved": count("approved")}


def open_review_list(p, status):
    """status: 'moderated' (Pending) or 'approved'."""
    links = _status_links(p, status)
    assert links, f"no {STATUS_LABELS[status]} link on the Reviews page"
    p.click(links[0])
    p.wait.until(lambda d: f"comment_status={status}" in d.current_url
                 or "current" in (_status_links(p, status)[0].get_attribute("class") or ""))
    p.present("#the-comment-list")


def review_row_xpath(author, product):
    return (
        "//tbody[@id='the-comment-list']/tr"
        f"[contains(normalize-space(.), '{author}') and contains(normalize-space(.), '{product}')]"
    )


def find_review_row(p, author, product):
    row = p.find_x(review_row_xpath(author, product))
    # The Rating column shows ★★★★★ with an aria-label such as "5 out of 5".
    labelled = row.find_elements(By.CSS_SELECTOR, "td.column-rating [aria-label], .star-rating")
    cells = row.find_elements(By.CSS_SELECTOR, "td.column-rating")
    label = labelled[0].get_attribute("aria-label") if labelled else ""
    shown = norm(cells[0].get_attribute("textContent")) if cells else ""
    m = re.search(r"(\d)(?:\.\d+)? out of 5", label or shown)
    stars = int(m.group(1)) if m else shown.count("★")
    return {"row": row, "text": norm(row.text), "stars": stars}


def approve_review(p, row):
    # Row actions (Approve, Reply, ...) only appear on hover, so click the link with JS.
    p.js_click(row.find_element(By.CSS_SELECTOR, "span.approve a"))

    def done(d):
        try:
            return (not row.is_displayed()) or "approved" in (row.get_attribute("class") or "").split()
        except StaleElementReferenceException:
            return True

    p.wait.until(done, message="review was not approved")