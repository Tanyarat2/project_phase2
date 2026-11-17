import os
import re
from collections import defaultdict
from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4

import pytest
import requests


SHOP_API = 'http://157.85.102.236/shop/wp-json/wc/v3'
PRODUCTS = '/products'


class ShopAPI:
    def __init__(self, session):
        self.session = session

    def check(self, method, path, status, expected, *, params=None, payload=None):
        query = f'?{urlencode(params)}' if params else ''
        print(f'Request: {method} {SHOP_API}{path}{query}')
        if payload is not None:
            print(f'JSON body: {payload}')
        print(f'Expected: HTTP {status} with {expected}')
        try:
            response = self.session.request(
                method, SHOP_API + path, params=params, json=payload,
                timeout=30, allow_redirects=False,
            )
        except requests.RequestException as error:
            raise AssertionError(f'Actual: no response ({type(error).__name__})') from None

        print(f'Actual: HTTP {response.status_code} with {response.text[:2500]}')
        assert response.status_code == status
        assert response.headers.get('Content-Type', '').startswith('application/json')
        return response.json()

    def assert_product(self, body, expected):
        assert isinstance(body, dict)
        assert type(body['id']) is int and body['id'] > 0
        if 'id' in expected:
            assert body['id'] == expected['id']
        for field in ('name', 'sku', 'type', 'status'):
            assert body[field] == expected[field], field
        assert isinstance(body['regular_price'], str)
        assert Decimal(body['regular_price']) == Decimal(expected['regular_price'])

    def assert_error(self, body, status, code, field=None):
        assert isinstance(body, dict)
        assert body['code'] == code
        assert isinstance(body['message'], str) and body['message'].strip()
        assert body['data']['status'] == status
        if field is not None:
            assert body['data']['params'][field]


@pytest.fixture(scope='session')
def credentials():
    username = os.environ.get('WC_SHOP_USERNAME', '').strip()
    password = os.environ.get('WC_SHOP_API_PASSWORD', '').strip()
    if not username or not password:
        pytest.skip('Missing shop username or Shop API password')
    match = re.fullmatch(r'itcs386-g([0-9]+)', username, flags=re.IGNORECASE)
    if match is None:
        pytest.exit('Enter your ITCS386 shop username, for example itcs386-g02.', returncode=2)
    group = f'G{match[1].zfill(2)}'
    return username, password, group


@pytest.fixture(scope='session')
def api(credentials):
    username, password, _ = credentials
    with requests.Session() as session:
        session.auth = (username, password)
        yield ShopAPI(session)


class ProductFixtures:
    def __init__(self, api, group):
        self.api = api
        self.group = group
        self.created_ids = set()
        self.unconfirmed = defaultdict(set)

    def new_sku(self):
        return f'{self.group}-api-{uuid4().hex}'

    def payload(self, **overrides):
        sku = self.new_sku()
        return {
            'name': f'{self.group} API Product {sku[-12:]}',
            'sku': sku,
            'type': 'simple',
            'status': 'draft',
            'regular_price': '125.50',
            **overrides,
        }

    def post(self, payload, status, expected):
        sku, name = payload['sku'], payload['name']
        self.unconfirmed[sku].add(name)
        body = self.api.check('POST', PRODUCTS, status, expected, payload=payload)
        if (
            status == 201 and isinstance(body, dict) and body.get('sku') == sku
            and body.get('name') == name and type(body.get('id')) is int and body['id'] > 0
        ):
            self.created_ids.add(body['id'])
            self.unconfirmed[sku].remove(name)
        return body

    def create(self):
        payload = self.payload()
        body = self.post(payload, 201, f'a new draft product matching {payload}')
        self.api.assert_product(body, payload)
        return body

    def delete(self, product_id):
        body = self.api.check(
            'DELETE', f'{PRODUCTS}/{product_id}', 200,
            f'the deleted test product ID {product_id}', params={'force': 'true'},
        )
        assert isinstance(body, dict) and body.get('id') == product_id
        self.created_ids.discard(product_id)

    def clean_up(self):
        # Recover any test products whose POST response did not confirm creation.
        errors = []
        for sku, names in self.unconfirmed.items():
            if not names:
                continue
            try:
                rows = self.api.check(
                    'GET', PRODUCTS, 200, 'a JSON list for the test SKU',
                    params={'sku': sku, 'per_page': 100},
                )
                assert isinstance(rows, list)
                for row in rows:
                    if row.get('sku') == sku and row.get('name') in names:
                        self.created_ids.add(row['id'])
            except (AssertionError, ValueError, KeyError, AttributeError):
                errors.append(f'Could not check for leftover test products with SKU {sku}.')

        for product_id in sorted(self.created_ids):
            try:
                self.delete(product_id)
            except (AssertionError, ValueError):
                errors.append(f'Could not delete test product ID {product_id}.')
        assert not errors, '\n'.join(errors)


@pytest.fixture
def products(api, credentials):
    _, _, group = credentials
    owned = ProductFixtures(api, group)
    yield owned
    owned.clean_up()
