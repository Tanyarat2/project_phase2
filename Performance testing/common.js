import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Public storefront only. No login, cart mutation, checkout, or order creation.
const BASE_URL = (__ENV.BASE_URL || 'http://157.85.102.236/shop').replace(/\/+$/, '');
const STORE_API = `${BASE_URL}/wp-json/wc/store/v1`;
const flowFailed = new Rate('shop_flow_failed');

export const thresholds = {
  http_req_duration: ['p(95)<1000'],
  http_req_failed: ['rate<0.02'],
  checks: ['rate>0.98'],
  shop_flow_failed: ['rate<0.02'],
};

// Ask k6 to retain per-load-level metrics in summary.json.
export function withScenarioThresholds(names) {
  const result = { ...thresholds };
  for (const name of names) {
    result[`http_req_duration{scenario:${name}}`] = ['p(95)<1000'];
    result[`http_req_failed{scenario:${name}}`] = ['rate<0.02'];
  }
  return result;
}

function jsonOrNull(response) {
  try {
    return response.json();
  } catch (_) {
    return null;
  }
}

function get(url, step, extraTags) {
  return http.get(url, {
    timeout: '15s',
    tags: { step, ...extraTags },
    headers: { Accept: 'application/json, text/html' },
  });
}

// Simulates a real customer's read-only journey, using currently listed products.
// There are no hardcoded product IDs; other groups may change the catalogue.
export function shopJourney(extraTags = {}) {
  let valid = true;

  const home = get(`${BASE_URL}/`, 'open_storefront', extraTags);
  valid = check(home, { 'storefront returns HTTP 200': (r) => r.status === 200 }) && valid;

  const listing = get(`${STORE_API}/products?per_page=6`, 'browse_products', extraTags);
  const products = jsonOrNull(listing);
  valid = check(listing, {
    'product listing returns HTTP 200': (r) => r.status === 200,
    'product listing contains products': () => Array.isArray(products) && products.length > 0,
  }) && valid;

  if (Array.isArray(products) && products.length > 0) {
    const product = products[Math.floor(Math.random() * products.length)];
    const keyword = typeof product.name === 'string' ? product.name.trim().split(/\s+/)[0] : '';
    const search = get(`${STORE_API}/products?search=${encodeURIComponent(keyword || 'G02')}&per_page=6`, 'search_products', extraTags);
    const found = jsonOrNull(search);
    valid = check(search, {
      'search returns HTTP 200': (r) => r.status === 200,
      'search returns JSON array': () => Array.isArray(found),
    }) && valid;

    if (Number.isInteger(product.id) && product.id > 0) {
      const detail = get(`${STORE_API}/products/${product.id}`, 'view_product_detail', extraTags);
      const body = jsonOrNull(detail);
      valid = check(detail, {
        'product detail returns HTTP 200': (r) => r.status === 200,
        'product detail ID matches listing': () => body !== null && body.id === product.id,
      }) && valid;

      // WordPress permalink can differ between installations; follow only same-shop URLs.
      if (typeof product.permalink === 'string' && product.permalink.startsWith(`${BASE_URL}/`)) {
        const page = get(product.permalink, 'view_product_page', extraTags);
        valid = check(page, { 'product page returns HTTP 200': (r) => r.status === 200 }) && valid;
      }
    } else {
      valid = false;
    }
  }

  flowFailed.add(valid ? 0 : 1);
  sleep(1.5 + Math.random()); // Human think time; limits unnecessary shared-server traffic.
}
