# Check that a simple product with a new SKU is created with the submitted fields.
def test_c01_create_with_unique_sku(api, products):
    payload = products.payload()
    body = products.post(payload, 201, f'a new product matching {payload}')
    api.assert_product(body, payload)


# Check that a second product cannot reuse the SKU of this test's first product.
def test_c02_reject_duplicate_sku(api, products):
    original = products.create()
    payload = products.payload(sku=original['sku'])
    body = products.post(payload, 400, 'the product_invalid_sku error')
    api.assert_error(body, 400, 'product_invalid_sku')


# Check that a product type outside the allowed values is rejected.
def test_c03_reject_invalid_type(api, products):
    payload = products.payload(type='unsupported-type')
    body = products.post(payload, 400, 'the rest_invalid_param error for type')
    api.assert_error(body, 400, 'rest_invalid_param', field='type')
