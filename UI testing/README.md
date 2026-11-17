# UI testing (Automated UI tests, Group G02)

Three automated UI tests written with **Selenium WebDriver (Python) + pytest**. Each one follows the steps of one system test case and checks the same expected results on the page.

| Automated test | Comes from | What it shows |
|---|---|---|
| `test_tc_sys_01_coupon_checkout.py` | TC-SYS-01 | Staff creates a product (฿500, stock 10) and a 10% coupon. A guest is stopped by quantity 0, an invalid coupon, the same coupon twice and an empty Town/City, then buys 2 for ฿900 by cash on delivery. Staff sees the order, stock 8 and coupon usage 1, and completes the order. The guest then sees "Order completed". |
| `test_tc_sys_02_stock_limit_cancel.py` | TC-SYS-02 | Staff creates an Accessories product with stock 3. A guest finds it under Accessories → Sort by latest, is stopped from adding 4, cannot set 0 in the cart, and buys 2 for ฿600. Staff sees stock 1, cancels the order, and stock is back at 3. The guest then sees "Order cancelled". |
| `test_tc_sys_03_review_moderation.py` | TC-SYS-03 | Staff creates a product. A guest's review is refused without a rating and with an invalid email, then held for approval. Staff approves it from Pending, and the guest then sees it published with 5 stars and "Reviews (1)". |

## How the tests are built

- **Two browsers per test.** The `staff` fixture is a normal Chrome window that logs in to WordPress Admin. The `customer` fixture is a separate incognito Chrome window, so the customer is a guest with an empty cart.
- **Stable locators.** IDs and names are used where the page has them (`#title`, `#_regular_price`, `#_stock`, `#billing-city`, `#order_status`, `#comment`, ...). Where it has none, the tests use WooCommerce's own block class names (`.wc-block-cart-items__row`, `.wc-block-components-totals-footer-item`, ...) and the product name created in the test.
- **No fixed pauses.** Every wait is a `WebDriverWait` for an element, a text or a URL. `time.sleep` is not used anywhere.
- **New data every run.** All names include the run date and time (`RUNID = YYYYMMDD-HHMMSS`), for example `G02-Test-Watch-20261116-153012`, `g02save10-20261116-153012` and `g02.sys01.20261116-153012@example.com`. So every test also passes on its second and later runs. Seconds are added so two runs in the same minute do not clash.
- **Only our own data.** Every record starts with `G02`, and the tests only change orders and reviews that they created themselves.
- **Evidence.** Each checked step saves a screenshot to `screenshots/<test name>/stepNN-<what>-<staff|customer>.png`. If a test fails, `FAILED-staff.png` and `FAILED-customer.png` show where it stopped.

```
UI testing/
├── README.md
├── requirements.txt
├── pytest.ini
├── conftest.py             
├── .env.example            
├── pages/
│   ├── base.py             
│   ├── staff.py            
│   └── customer.py         
├── test_tc_sys_01_coupon_checkout.py
├── test_tc_sys_02_stock_limit_cancel.py
├── test_tc_sys_03_review_moderation.py
└── screenshots/           
```

## How to run the tests

Requirements: Python 3.10 or newer and Google Chrome. Selenium downloads the matching ChromeDriver by itself.

```bash
cd "project_phase2/UI testing"
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # Windows: copy .env.example .env
# open .env and fill in G02_STAFF_USER and G02_STAFF_PASSWORD
```

Run all three tests and also save an HTML report:

```bash
pytest --html=report.html --self-contained-html
```

Run a single test:

```bash
pytest test_tc_sys_01_coupon_checkout.py
```

Run without opening browser windows:

```bash
HEADLESS=1 pytest              # Windows PowerShell: $env:HEADLESS="1"; pytest
```

To show that the tests pass on every run, run the suite twice in a row. Each run creates new data, so both runs pass:

```bash
pytest && pytest
```

- **Recording.** In addition to the screenshots, a screen recording of a full run is linked here: `<https://drive.google.com/drive/folders/16xQMdS-swOEKb0qY0ahKituVIeLVvO9D?usp=sharing>`.

## Results

Run on 17 Nov 2026 with `python -m pytest`, twice in a row:

| Run | Result | Output |
|---|---|---|
| 1 | 3 passed in 119.37s | run-1.txt, report.html |
| 2 | 3 passed in 112.33s | run-2.txt |

Each run used new data (RUNIDs in run-ids.txt), so all tests pass on every run.
