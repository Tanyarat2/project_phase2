import pytest

from conftest import PRODUCTS


# Check that the valid lower page-size limit returns only the first matching product.
def test_l01_list_at_minimum_page_size(api, products):
    first, second = products.create(), products.create()
    params = {'sku': f'{first["sku"]},{second["sku"]}', 'per_page': 1, 'orderby': 'id', 'order': 'asc'}
    body = api.check('GET', PRODUCTS, 200, f'a list containing only product {first["id"]}', params=params)
    assert isinstance(body, list) and len(body) == 1
    api.assert_product(body[0], first)


# Check that the valid upper page-size limit returns both matching products in ID order.
def test_l02_list_at_maximum_page_size(api, products):
    first, second = products.create(), products.create()
    params = {'sku': f'{first["sku"]},{second["sku"]}', 'per_page': 100, 'orderby': 'id', 'order': 'asc'}
    body = api.check(
        'GET', PRODUCTS, 200, f'a list containing products {first["id"]} and {second["id"]}',
        params=params,
    )
    assert isinstance(body, list) and len(body) == 2
    api.assert_product(body[0], first)
    api.assert_product(body[1], second)


# Check that a unique, unused SKU returns an empty array with the default page size.
def test_l03_list_no_matching_sku(api, products):
    body = api.check('GET', PRODUCTS, 200, 'an empty list', params={'sku': products.new_sku()})
    assert body == []


# Check that each invalid page-size partition returns a validation error for per_page.
@pytest.mark.parametrize('page_size', [0, 101, 'abc'], ids=['L04-below-min', 'L05-above-max', 'L06-text'])
def test_list_rejects_invalid_page_size(api, page_size):
    body = api.check(
        'GET', PRODUCTS, 400, 'the rest_invalid_param error for per_page',
        params={'per_page': page_size},
    )
    api.assert_error(body, 400, 'rest_invalid_param', field='per_page')
