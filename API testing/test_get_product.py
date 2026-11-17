from conftest import PRODUCTS


# Check that a valid ID returns the exact product created by this test.
def test_g01_get_existing_product(api, products):
    product = products.create()
    body = api.check('GET', f'{PRODUCTS}/{product["id"]}', 200, f'the product {product["id"]}')
    api.assert_product(body, product)


# Check that a valid numeric ID for a deleted product returns a product-not-found error.
def test_g02_get_deleted_product(api, products):
    product_id = products.create()['id']
    products.delete(product_id)
    body = api.check(
        'GET', f'{PRODUCTS}/{product_id}', 404, 'the woocommerce_rest_product_invalid_id error',
    )
    api.assert_error(body, 404, 'woocommerce_rest_product_invalid_id')


# Check that a nonnumeric ID cannot match the product route.
def test_g03_reject_nonnumeric_id(api):
    body = api.check('GET', f'{PRODUCTS}/abc', 404, 'the rest_no_route error')
    api.assert_error(body, 404, 'rest_no_route')
