# project_phase2

# API Testing

The system is the [course shop](http://157.85.102.236/shop/), and the REST API base URL is `http://157.85.102.236/shop/wp-json/wc/v3`.

The tests use **pytest** and **Requests**. Each of the three operations has its own test suite; creating a product is the operation that changes data.

| Operation | Endpoint | Test suite | Cases |
| --- | --- | --- | ---: |
| Create a product | `POST /products` | [test_create_product.py](API%20testing/test_create_product.py) | 3 |
| Retrieve a product | `GET /products/{id}` | [test_get_product.py](API%20testing/test_get_product.py) | 3 |
| List products | `GET /products` | [test_list_products.py](API%20testing/test_list_products.py) | 6 |

Shared authentication, response checks, and test-data setup and cleanup are in [conftest.py](API%20testing/conftest.py). Each test has a short comment explaining its goal and checks both the HTTP status and important response fields. All responses must have a JSON content type.

## Test case design

We used **input space partitioning** to derive the cases:

1. Identify the inputs that affect each operation: SKU and product type for creation, product ID for retrieval, and SKU filter and page size for listing.
2. Divide those inputs into valid and invalid partitions, such as a new versus duplicate SKU, or a numeric versus nonnumeric ID. For valid numeric IDs, distinguish existing and missing products.
3. Select a representative from each chosen partition while keeping other inputs valid. For `per_page`, also apply **boundary value analysis** at `1` and `100`, and immediately outside those limits at `0` and `101`.

The tables below map the partitions to the implemented cases and expected responses. These are selected partitions for the three operations, rather than exhaustive coverage of every API field or input combination.

### Create a product - `POST /products`

We partitioned SKU by whether it is new or already in use, and product type by whether it belongs to the allowed list. We hold the name, draft status and price to valid values.

| Case | Input partition and representative | Expected HTTP status and response |
| --- | --- | --- |
| C01 | New SKU and allowed type `simple` | `201`. Positive integer ID and matching name, SKU, type, draft status and regular price `125.50`. |
| C02 | Duplicate SKU from this test's own draft product | `400`. `product_invalid_sku`, a nonempty message and `data.status` of `400`. |
| C03 | New SKU and an unsupported type, `unsupported-type` | `400`. `rest_invalid_param`, a nonempty message, `data.status` of `400` and `data.params.type`. |

### Retrieve a product - `GET /products/{id}`

We partitioned the ID by its format and, for numeric IDs, by whether the product exists. The missing numeric ID comes from deleting a product created by this case.

| Case | Input partition and representative | Expected HTTP status and response |
| --- | --- | --- |
| G01 | Existing numeric ID from a new draft product | `200`. Exact ID, name, SKU, type, draft status and regular price. |
| G02 | Numeric ID of the test's deleted product | `404`. `woocommerce_rest_product_invalid_id`, a nonempty message and `data.status` of `404`. |
| G03 | Nonnumeric ID `abc` | `404`. `rest_no_route`, a nonempty message and `data.status` of `404`. |

### List products - `GET /products`

We partitioned the SKU filter by whether it matches any records. For `per_page`, we used the default, the valid integer range of 1 to 100, values outside either end of the range and a nonnumeric value. Tests with matches use two draft products and sort by ascending ID.

| Case | Input partition and representative | Expected HTTP status and response |
| --- | --- | --- |
| L01 | Matching SKUs and `per_page=1`, the minimum | `200`. One product with the first ID and matching product fields. |
| L02 | Matching SKUs and `per_page=100`, the maximum | `200`. Both products in ID order, with matching product fields. |
| L03 | Unused SKU and omitted `per_page` | `200`. An empty JSON array. |
| L04 | `per_page=0`, below the minimum | `400`. `rest_invalid_param`, a nonempty message, `data.status` of `400` and `data.params.per_page`. |
| L05 | `per_page=101`, above the maximum | `400`. `rest_invalid_param`, a nonempty message, `data.status` of `400` and `data.params.per_page`. |
| L06 | `per_page=abc`, nonnumeric | `400`. `rest_invalid_param`, a nonempty message, `data.status` of `400` and `data.params.per_page`. |

## Run all 12 cases

Install Python 3.10 or newer and have your group's course shop username and **Shop API password** available. From the `project phase 2` folder, install the dependencies in [requirements.txt](API%20testing/requirements.txt) once:

```powershell
py -m pip install -r "API testing/requirements.txt"
```

Run all three suites with one command:

```powershell
py "API testing/run_api_tests.py"
```

On macOS or Linux, use `python3` in both commands. Enter your ITCS386 shop username (for example, `itcs386-g02`) and the value in the **Shop API password** column of the instructor's accounts sheet. The runner uses HTTP Basic authentication with the Shop API password, which is your group's WordPress Application Password. The sheet's regular **Password** column is for browser login. The runner takes the group number from the username and hides the Shop API password as you type or paste. For a noninteractive run, set `WC_SHOP_USERNAME` and `WC_SHOP_API_PASSWORD` in the environment. Keep your Shop API password out of GitHub.

The command runs all three suites and saves the output to [API testing/results.txt](API%20testing/results.txt), replacing the previous log. A successful run reports `12 passed` and `Runner exit code: 0`. Missing credentials cause the tests to be skipped and the runner to return a nonzero exit code; skipped tests are not evidence of a successful live run.

## Results

The saved full-run output in [results.txt](API%20testing/results.txt) records a start time of **17 November 2026 at 19:02:08 Thailand time (UTC+7)**. All **12 cases passed in 4.23 seconds**, and the runner finished with exit code `0`.

| Operation | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Create a product | 3 | 0 | 0 |
| Retrieve a product | 3 | 0 | 0 |
| List products | 6 | 0 | 0 |
| **Total** | **12** | **0** | **0** |

The shop returned the expected fields for valid product requests and the expected errors for a duplicate SKU, an invalid product type, missing and malformed IDs, and invalid page sizes. An expected `400` or `404` response passes its test when its status and error fields match the assertions. The recorded run found no defects in these tested cases; it does not establish that the entire API is defect-free.

There were no failing tests to classify as system defects or test mistakes. If a later run fails, record that classification for each failure. For a system defect, include the request, expected result, and actual result, as required by the assignment.

<!-- ITCS386_PERFORMANCE_BEGIN -->
## Performance Testing (k6) — Group 02

Four k6 workloads cover Average-load, Stress, Soak and Spike on the shared WooCommerce shop. The full design, instructions, original k6 summaries and analyses are in **[Performance testing/README.md](Performance%20testing/README.md)**.

| Test | Recorded finding |
| :--- | :--- |
| Average-load (3 VUs, 2 min) | p95 **1,404.22 ms** — latency threshold breached |
| Extended Stress (up to 10 VUs) | Latest valid run: **7 VUs p95 974.77 ms (pass)**; **10 VUs p95 ~1.57 s (fail)**; 0 HTTP errors and 100% functional checks. A separate run breached p95 at 7 VUs, so the boundary is variable. |
| Soak (2 VUs, 15 min) | p95 **875.79 ms** overall; **2/2,510 HTTP failures**; no progressive degradation observed |
| Spike (1 → 6 → 1 VUs) | p95 **1,121.82 ms** overall; stable recovery was **not confirmed within 120 s** |

The shared-server results vary by run. Do not equate `vus_max` with server capacity or interpret HTTP 200 as functional success without content checks. **Original `summary.json` outputs are retained as evidence.**
<!-- ITCS386_PERFORMANCE_END -->
