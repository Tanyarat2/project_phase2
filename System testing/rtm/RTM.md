# Requirement Traceability Matrix (RTM)

[← Back to System testing](../README.md)

Each row is a feature of the WooCommerce shop. Each cell lists the steps of the test case that cover it (S = step). Test cases: [TC-SYS-01](../test-cases/TC-SYS-01.md) (30 steps), [TC-SYS-02](../test-cases/TC-SYS-02.md) (26 steps), [TC-SYS-03](../test-cases/TC-SYS-03.md) (19 steps).

## Staff side

| ID | Feature | TC-SYS-01 | TC-SYS-02 | TC-SYS-03 |
|---|---|---|---|---|
| F01 | Log in to WordPress Admin | S1 | S1 | S1 |
| F02 | Create and publish a simple product | S2–S6 | S2–S6 | S2–S6 |
| F03 | Set and track product stock | S4, S6 | S4, S6 | S4, S6 |
| F04 | Assign a product category | | S4, S6 | |
| F05 | Create a percentage discount coupon | S7–S10 | | |
| F06 | Find an order and view its details | S24–S26 | S19–S20, S22 | |
| F07 | Stock reduced automatically after an order | S27 | S21 | |
| F08 | Coupon usage count updated after an order | S28 | | |
| F09 | Change order status to Completed | S29 | | |
| F10 | Cancel an order and restore stock | | S23–S25 | |
| F11 | Moderate product reviews (view pending, approve) | | | S15–S18 |

## Customer side

| ID | Feature | TC-SYS-01 | TC-SYS-02 | TC-SYS-03 |
|---|---|---|---|---|
| F12 | Browse the shop as a guest | S11 | S7 | S7 |
| F13 | Find a product (search, sort by latest, category) | S12 | S8 | S8 |
| F14 | View product page (price, stock availability) | S12–S13 | S9 | S8 |
| F15 | Add to cart with quantity validation (0, more than stock) | S13–S14 | S10–S11 | |
| F16 | View cart and update quantity | S15, S20 | S12–S14 | |
| F17 | Apply a valid coupon | S17, S19 | | |
| F18 | Reject an invalid or already-applied coupon | S16, S18 | | |
| F19 | Guest checkout with Cash on delivery | S19, S21–S22 | S15–S17 | |
| F20 | Checkout required-field validation | S21 | | |
| F21 | Cart and coupon kept when going back from checkout | S20 | | |
| F22 | Order received (confirmation) page | S22–S23 | S17–S18 | |
| F23 | Customer sees the order status change | S30 | S26 | |
| F24 | Submit a product review with validation (no rating, invalid email) | | | S9–S13 |
| F25 | Review held for approval, then shown publicly | | | S13–S14, S19 |

## Coverage summary

| Test case | Staff features | Customer features | Total features |
|---|---:|---:|---:|
| TC-SYS-01 | 8 | 12 | 20 |
| TC-SYS-02 | 7 | 8 | 15 |
| TC-SYS-03 | 4 | 5 | 9 |

Every feature F01–F25 is covered by at least one test case.

## Not covered by system tests

These shop features are not part of the three scenarios:

- Customer registration, login and My Account
- Customer order history in My Account
- Order notes to the customer
- Shipping methods (the shop uses Cash on delivery only)

Before submission, rename the features to match the shop guide on MyCourses. Add any feature from the guide that is missing, to this list or to the tables.
