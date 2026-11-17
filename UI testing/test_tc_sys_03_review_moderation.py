"""Automated version of TC-SYS-03: Product Review Submission and Moderation."""
from selenium.webdriver.support import expected_conditions as EC

from pages import customer as C
from pages import staff as S
from pages.base import make_run_id, step

REVIEW_TEXT = "The product quality is excellent."
AUTHOR = "G02 SYS03Tester"
# Passes the browser's own email check (it has an @) but fails WordPress's check
# (the domain has no dot), so WordPress shows its error page as TC-SYS-03 step 11 expects.
INVALID_EMAIL = "g02-invalid-email@nodot"


# Goal (TC-SYS-03): staff creates a product; a guest's review is refused without a rating and
# with an invalid email, then accepted and held for approval (count stays 0); staff finds it in
# Pending, approves it, and sees it in Approved; the guest then sees the review published with
# 5 stars and the tab shows Reviews (1).
def test_tc_sys_03_review_moderation(staff, customer):
    run = make_run_id()
    product = f"G02-Review-Test-Product-{run}"
    email = f"g02.sys03.{run}@example.com"
    print(f"\nRUNID={run}  product={product}")

    # ---------------- Staff: product ----------------
    step(1, "staff logs in")
    login = S.login(staff)
    assert login["in_admin"] and login["dashboard_menu"]
    staff.shot("step01-dashboard")

    step(2, "Products menu")
    submenu = S.click_products_menu(staff)
    assert "all products" in submenu.lower() and "add new" in submenu.lower()
    staff.shot("step02-products-menu")

    step(3, "Add New Product")
    page = S.click_add_new_product(staff)
    assert page["title_field"] and page["description_editor"]
    staff.shot("step03-add-product")

    step(4, "fill product data")
    form = S.fill_product(staff, product, 350, 10)
    assert form == {"type": "simple", "price": "350", "manage_stock": True,
                    "stock": "10", "category_ticked": None}
    staff.shot("step04-product-form")

    step(5, "publish product")
    assert "Product published." in S.publish_product(staff)
    staff.shot("step05-product-published")

    step(6, "product in All Products")
    row = S.find_product_row(staff, product)
    assert row["price"] == "฿350.00"
    assert row["stock"] == "In stock (10)"
    staff.shot("step06-product-list")

    # ---------------- Customer: review ----------------
    step(7, "guest opens the shop")
    home = C.open_home(customer)
    assert home["product_cards"] > 0 and not home["logged_in"]
    customer.shot("step07-home")

    step(8, "open the product")
    C.search_product(customer, product)
    info = C.open_product_from_list(customer, product)
    assert info["name"] == product
    assert info["price"] == "฿350.00"
    customer.shot("step08-product")

    step(9, "Reviews tab is empty")
    C.open_reviews_tab(customer)
    customer.wait_text(".woocommerce-noreviews", "There are no reviews yet.")
    for field in ("#rating", "#comment", "#author", "#email"):
        customer.present(field)
    customer.shot("step09-reviews-tab")

    step(10, "submit without a rating")
    C.fill_review(customer, None, REVIEW_TEXT, AUTHOR, email)
    C.submit_review(customer)
    alert = customer.wait.until(EC.alert_is_present())
    print(f"    popup: {alert.text!r}")
    assert alert.text == "Please select a rating"
    alert.accept()
    assert "/product/" in customer.d.current_url
    customer.shot("step10-no-rating-after-popup")

    step(11, "5 stars + invalid email")
    C.fill_review(customer, 5, REVIEW_TEXT, AUTHOR, INVALID_EMAIL)
    assert C.selected_rating(customer) == "5"
    C.submit_review(customer)
    customer.wait.until(lambda d: "wp-comments-post.php" in d.current_url)
    customer.wait_body("Error: Please enter a valid email address.")
    customer.shot("step11-invalid-email-error")

    step(12, "browser Back")
    customer.d.back()
    customer.present("#commentform")
    C.open_reviews_tab(customer)
    customer.find("#commentform")
    customer.shot("step12-back")

    step(13, "valid review")
    C.fill_review(customer, 5, REVIEW_TEXT, AUTHOR, email)
    assert C.selected_rating(customer) == "5"
    C.submit_review(customer)
    customer.wait.until(lambda d: "wp-comments-post.php" not in d.current_url and "/product/" in d.current_url)
    C.open_reviews_tab(customer)
    customer.wait_text(".woocommerce-review__awaiting-approval", "Your review is awaiting approval")
    customer.shot("step13-awaiting-approval")

    # ---------------- Staff: moderation ----------------
    step(14, "review marked as awaiting, count still 0")
    review = C.review_item(customer, REVIEW_TEXT)
    assert "awaiting approval" in review["awaiting"]
    assert C.reviews_tab_title(customer) == "Reviews (0)"
    staff.shot("step14-reviews-tab")

    step(15, "Products > Reviews")
    assert S.open_reviews(staff)["pending_link"]
    before = S.review_counts(staff)
    print(f"    counts before: {before}")
    staff.shot("step15-reviews-page")

    step(16, "review is in Pending")
    S.open_review_list(staff, "moderated")
    pending = S.find_review_row(staff, AUTHOR, product)
    assert REVIEW_TEXT in pending["text"]
    assert pending["stars"] == 5
    staff.shot("step16-pending")

    step(17, "approve it")
    S.approve_review(staff, pending["row"])
    S.open_reviews(staff)
    S.open_review_list(staff, "moderated")
    assert staff.d.find_elements("xpath", S.review_row_xpath(AUTHOR, product)) == []
    after = S.review_counts(staff)
    print(f"    counts after: {after}")
    # The server is shared by every group, so other reviews may be approved at the same time.
    assert after["approved"] >= before["approved"] + 1
    staff.shot("step17-approved")

    step(18, "review is in Approved")
    S.open_review_list(staff, "approved")
    approved = S.find_review_row(staff, AUTHOR, product)
    assert REVIEW_TEXT in approved["text"]
    assert approved["stars"] == 5
    staff.shot("step18-approved-list")

    # ---------------- Customer: sees the review ----------------
    step(19, "guest refreshes the product page")
    customer.d.refresh()
    C.open_reviews_tab(customer)
    customer.wait.until(lambda d: C.reviews_tab_title(customer) == "Reviews (1)")
    review = C.review_item(customer, REVIEW_TEXT)
    assert review["author"] == AUTHOR
    assert review["rating"] == "Rated 5 out of 5"
    assert review["awaiting"] == ""
    customer.shot("step19-review-published")