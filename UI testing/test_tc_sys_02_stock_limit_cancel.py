"""Automated version of TC-SYS-02: Category Browsing, Stock Limit and Order Cancellation."""
from pages import customer as C
from pages import staff as S
from pages.base import make_run_id, step


# Goal (TC-SYS-02): staff creates an Accessories product with only 3 in stock; a guest finds it
# through the Accessories category (Sort by latest), is stopped from adding 4, adds 2, cannot set
# 0 in the cart, and checks out by cash on delivery; staff sees stock drop to 1, cancels the
# order, sees stock back at 3, and the guest's confirmation page then shows "Order cancelled".
def test_tc_sys_02_stock_limit_and_cancel(staff, customer):
    run = make_run_id()
    product = f"G02-Limited-Stock-Product-{run}"
    billing = {
        "email": f"g02.sys02.{run}@example.com",
        "first": "G02",
        "last": "SYS02Tester",
        "phone": "0800000000",
        "address": "99 Test Road",
        "city": "Bangkok",
        "state": "TH-10",
        "postcode": "10400",
        "country": "TH",
    }
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

    step(4, "fill product data (stock 3, Accessories)")
    form = S.fill_product(staff, product, 300, 3, category="Accessories")
    assert form == {"type": "simple", "price": "300", "manage_stock": True,
                    "stock": "3", "category_ticked": True}
    staff.shot("step04-product-form")

    step(5, "publish product")
    assert "Product published." in S.publish_product(staff)
    staff.shot("step05-product-published")

    step(6, "product in All Products")
    row = S.find_product_row(staff, product)
    assert row["price"] == "฿300.00"
    assert "Accessories" in row["categories"]
    assert row["stock"] == "In stock (3)"
    staff.shot("step06-product-list")

    # ---------------- Customer ----------------
    step(7, "guest opens the shop")
    home = C.open_home(customer)
    assert home["product_cards"] > 0 and not home["logged_in"]
    customer.shot("step07-home")

    step(8, "Accessories category, Sort by latest")
    C.open_category(customer, "accessories", "Accessories")
    C.sort_by(customer, "date")
    customer.wait.until(lambda d: C.list_names(customer)[:1] == [product],
                        message="newest Accessories product is not the G02 product")
    assert all("product_cat-accessories" in cls for cls in C.list_classes(customer))
    assert C.card_price(customer, product) == "฿300.00"
    customer.shot("step08-category-latest")

    step(9, "product page shows 3 in stock")
    info = C.open_product_from_list(customer, product)
    assert info["name"] == product
    assert info["price"] == "฿300.00"
    assert "3 in stock" in info["body"]
    customer.shot("step09-product")

    step(10, "quantity 4 is blocked")
    qty = C.add_to_cart(customer, 4)
    v = customer.validity(qty)
    print(f"    browser message: {v['message']!r}")
    assert qty.get_attribute("max") == "3"
    assert v["overflow"] and not v["valid"]
    if v["message"].isascii():
        assert v["message"] == "Value must be less than or equal to 3."
    assert C.cart_count(customer) == 0
    customer.shot("step10-qty-4-blocked")

    step(11, "add quantity 2")
    C.add_to_cart(customer, 2)
    assert "added to your cart" in C.wait_added_notice(customer)
    C.wait_cart_count(customer, 2)
    customer.shot("step11-added")

    step(12, "cart shows qty 2, ฿600.00")
    C.open_cart(customer)
    line = C.cart_line(customer, product)
    assert line["qty"] == "2"
    assert line["line_total"] == "฿600.00"
    customer.shot("step12-cart")

    step(13, "quantity 0 in the cart resets to 1")
    C.set_cart_qty(customer, product, 0)
    C.wait_cart_qty(customer, product, 1)
    C.wait_line_total(customer, product, "฿300.00")
    assert C.cart_line(customer, product)["lines"] >= 1
    customer.shot("step13-qty-zero-reset")

    step(14, "quantity back to 2")
    C.set_cart_qty(customer, product, 2)
    C.wait_cart_qty(customer, product, 2)
    C.wait_line_total(customer, product, "฿600.00")
    C.wait_total(customer, "฿600.00")
    customer.shot("step14-qty-2")

    step(15, "checkout page")
    C.proceed_to_checkout(customer)
    summary = C.checkout_summary(customer)
    assert summary["items"] == [(product, "2")]
    assert summary["total"] == "฿600.00"
    assert summary["cod_available"]
    customer.shot("step15-checkout")

    step(16, "billing details + Cash on delivery")
    assert C.fill_checkout(customer, billing)
    assert C.field_errors(customer) == []
    customer.shot("step16-billing")

    step(17, "place order")
    C.place_order(customer)
    order_id = C.wait_order_received(customer)
    body = customer.body()
    assert product in body and "× 2" in body
    assert "฿600.00" in body and "Cash on delivery" in body
    customer.shot("step17-order-placed")

    step(18, f"order number {order_id}")
    assert str(order_id) in body
    customer.shot("step18-order-received")

    # ---------------- Staff ----------------
    step(19, "WooCommerce > Orders")
    assert "Orders" in S.open_orders(staff)
    staff.shot("step19-orders-page")

    step(20, "open the order")
    order = S.open_order(staff, order_id)
    assert order["status"] == "wc-processing"
    assert billing["email"] in order["data"]
    assert "Cash on delivery" in order["data"]
    assert product in order["items"] and "× 2" in order["items"]
    assert "฿600.00" in order["items"]
    staff.shot("step20-order")

    step(21, "stock is now 1")
    assert S.find_product_row(staff, product)["stock"] == "In stock (1)"
    staff.shot("step21-stock-1")

    step(22, "open the order again")
    S.open_order(staff, order_id)
    staff.shot("step22-order-again")

    step(23, "cancel the order")
    message, order = S.set_order_status(staff, "Cancelled")
    assert "Order updated." in message
    assert order["status"] == "wc-cancelled"
    staff.shot("step23-cancelled")

    step(24, "stock restored to 3")
    assert S.find_product_row(staff, product)["stock"] == "In stock (3)"
    staff.shot("step24-stock-3")

    step(25, "order list shows Cancelled, details unchanged")
    listed = S.find_order_row(staff, order_id)
    assert listed["status"] == "Cancelled"
    assert "G02 SYS02Tester" in listed["text"]
    staff.shot("step25-order-list")
    order = S.open_order(staff, order_id)
    assert product in order["items"] and "× 2" in order["items"]
    assert billing["email"] in order["data"]
    staff.shot("step25-order-details")

    # ---------------- Customer ----------------
    step(26, "guest refreshes the confirmation page")
    customer.d.refresh()
    customer.wait_body("Order cancelled")
    body = customer.body()
    assert "Your order has been cancelled." in body
    assert str(order_id) in body and product in body
    customer.shot("step26-order-cancelled")