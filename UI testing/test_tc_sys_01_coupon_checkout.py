"""Automated version of TC-SYS-01: Product Creation and Purchase with Coupon (Guest Checkout)."""
from pages import customer as C
from pages import staff as S
from pages.base import make_run_id, step


# Goal (TC-SYS-01): staff creates a product (฿500, stock 10) and a 10% coupon; a guest buys
# 2 with the coupon by cash on delivery, and is stopped on the way by quantity 0, an invalid
# coupon, the same coupon twice and an empty Town/City; staff then sees the order (Processing,
# coupon -฿100, total ฿900), stock 8 and coupon usage 1, and completes it; the guest's
# confirmation page then shows "Order completed".
def test_tc_sys_01_coupon_guest_checkout(staff, customer):
    run = make_run_id()
    product = f"G02-Test-Watch-{run}"
    coupon = f"g02save10-{run}"
    billing = {
        "email": f"g02.sys01.{run}@example.com",
        "first": "G02",
        "last": "SYSTester",
        "phone": "0800000000",
        "address": "99 Test Road",
        "city": "Bangkok",
        "state": "TH-10",  # Bangkok
        "postcode": "10400",
        "country": "TH",
    }
    print(f"\nRUNID={run}  product={product}  coupon={coupon}")

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
    form = S.fill_product(staff, product, 500, 10)
    assert form == {"type": "simple", "price": "500", "manage_stock": True,
                    "stock": "10", "category_ticked": None}
    staff.shot("step04-product-form")

    step(5, "publish product")
    assert "Product published." in S.publish_product(staff)
    staff.shot("step05-product-published")

    step(6, "product in All Products")
    row = S.find_product_row(staff, product)
    assert row["price"] == "฿500.00"
    assert row["stock"] == "In stock (10)"
    staff.shot("step06-product-list")

    # ---------------- Staff: coupon ----------------
    step(7, "Add new coupon page")
    S.open_add_new_coupon(staff)
    staff.shot("step07-add-coupon-page")

    step(8, "fill coupon")
    form = S.fill_coupon(staff, coupon, "percent", 10)
    assert form == {"code": coupon, "type": "percent", "amount": "10"}
    staff.shot("step08-coupon-form")

    step(9, "publish coupon")
    message, status = S.publish_coupon(staff)
    assert "Coupon updated." in message
    assert status == "Published"
    staff.shot("step09-coupon-published")

    step(10, "coupon in Coupons list")
    crow = S.find_coupon_row(staff, coupon)
    assert crow["type"] == "Percentage discount"
    assert crow["amount"] == "10"
    assert crow["usage"].startswith("0")
    staff.shot("step10-coupon-list")

    # ---------------- Customer: shopping ----------------
    step(11, "guest opens the shop")
    home = C.open_home(customer)
    assert home["product_cards"] > 0 and not home["logged_in"]
    customer.shot("step11-home")

    step(12, "search for the product")
    found = C.search_product(customer, product)
    assert found["name"] == product
    assert found["price"] == "฿500.00"
    customer.shot("step12-search")

    step(13, "quantity 0 is blocked")
    C.open_product_from_list(customer, product)
    qty = C.add_to_cart(customer, 0)
    v = customer.validity(qty)
    print(f"    browser message: {v['message']!r}")
    assert v["underflow"] and not v["valid"]
    if v["message"].isascii():  # English browser
        assert v["message"] == "Value must be greater than or equal to 1."
    assert C.cart_count(customer) == 0
    customer.shot("step13-qty-zero-blocked")

    step(14, "add quantity 2")
    C.add_to_cart(customer, 2)
    assert "added to your cart" in C.wait_added_notice(customer)
    C.wait_cart_count(customer, 2)
    customer.shot("step14-added")

    step(15, "cart shows 1 line, qty 2, ฿1,000.00")
    C.open_cart(customer)
    line = C.cart_line(customer, product)
    assert line["lines"] == 1
    assert line["qty"] == "2"
    assert line["line_total"] == "฿1,000.00"
    assert line["total"] == "฿1,000.00"
    customer.shot("step15-cart")

    step(16, "invalid coupon rejected")
    C.apply_coupon(customer, "g02-invalid")
    error = C.wait_coupon_error(customer, "g02-invalid")
    print(f"    coupon error: {error!r}")
    assert "does not exist" in error or "not valid" in error
    C.wait_total(customer, "฿1,000.00")  # wait for the totals to finish refreshing
    assert C.discount(customer) is None
    customer.shot("step16-invalid-coupon")

    step(17, "valid coupon applied")
    C.apply_coupon(customer, coupon)
    assert C.wait_discount(customer, "฿100.00").startswith("-")
    C.wait_total(customer, "฿900.00")
    assert coupon in C.applied_coupons(customer)
    customer.shot("step17-coupon-applied")

    step(18, "same coupon again rejected")
    C.apply_coupon(customer, coupon)
    error = C.wait_coupon_error(customer, "already")
    print(f"    coupon error: {error!r}")
    assert "applied" in error
    # The cart totals briefly turn into grey loading bars after Apply, so wait for them.
    assert C.wait_discount(customer, "฿100.00") == "-฿100.00"
    C.wait_total(customer, "฿900.00")
    assert coupon in C.applied_coupons(customer)
    customer.shot("step18-coupon-twice")

    step(19, "checkout page")
    C.proceed_to_checkout(customer)
    summary = C.checkout_summary(customer)
    assert summary["items"] == [(product, "2")]
    assert summary["discount"] == "-฿100.00"
    assert summary["total"] == "฿900.00"
    assert summary["cod_available"]
    customer.shot("step19-checkout")

    step(20, "browser Back returns to the cart")
    customer.d.back()
    C.wait_cart_qty(customer, product, 2)
    assert coupon in C.applied_coupons(customer)
    C.wait_total(customer, "฿900.00")
    customer.shot("step20-back-to-cart")

    step(21, "empty Town/City is rejected")
    C.proceed_to_checkout(customer)
    C.fill_checkout(customer, billing, city="")
    C.place_order(customer)
    city_error = C.wait_city_error(customer)
    print(f"    city error: {city_error!r}")
    assert city_error
    assert "/checkout/" in customer.d.current_url and "order-received" not in customer.d.current_url
    customer.shot("step21-city-required")

    step(22, "order placed")
    customer.fill("#billing-city", "Bangkok")
    assert C.select_cod(customer)
    C.place_order(customer)
    order_id = C.wait_order_received(customer)
    body = customer.body()
    assert product in body and "× 2" in body
    assert "฿900.00" in body
    assert "Cash on delivery" in body
    staff.shot("step22-order-placed")

    step(23, f"order number {order_id}")
    assert str(order_id) in body
    customer.shot("step23-order-received")

    # ---------------- Staff: check the order ----------------
    step(24, "WooCommerce > Orders")
    assert "Orders" in S.open_orders(staff)
    staff.shot("step24-orders-page")

    step(25, "open the order")
    order = S.open_order(staff, order_id)
    assert order["status"] == "wc-processing"
    assert billing["email"] in order["data"]
    assert product in order["items"] and "× 2" in order["items"]
    staff.shot("step25-order")

    step(26, "coupon, total and payment method")
    assert coupon in order["items"].lower()
    assert "฿100.00" in order["items"]
    assert "฿900.00" in order["items"]
    assert "Cash on delivery" in order["data"]
    staff.shot("step26-order-details")

    step(27, "stock is now 8")
    assert S.find_product_row(staff, product)["stock"] == "In stock (8)"
    staff.shot("step27-stock-8")

    step(28, "coupon used once")
    assert S.find_coupon_row(staff, coupon)["usage"].startswith("1")
    staff.shot("step28-coupon-usage")

    step(29, "mark order Completed")
    S.open_order(staff, order_id)
    message, order = S.set_order_status(staff, "Completed")
    assert "Order updated." in message
    assert order["status"] == "wc-completed"
    staff.shot("step29-completed")

    # ---------------- Customer: sees the result ----------------
    step(30, "guest refreshes the confirmation page")
    customer.d.refresh()
    customer.wait_body("Order completed")
    body = customer.body()
    assert "Thank you. Your order has been fulfilled." in body
    assert str(order_id) in body and product in body and "฿900.00" in body
    customer.shot("step30-order-completed")