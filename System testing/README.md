# System Testing – Group G02
 
System under test: WooCommerce shop at http://157.85.102.236/shop/ (staff side: http://157.85.102.236/shop/wp-admin/). The shop uses the block-based cart and checkout, and Cash on delivery is the only payment method.
 
Three manual system test cases each follow one complete scenario across the staff side and the customer side. Each starts with a staff task and ends with what the customer and staff see as the result.
 
| Test case | Scenario | Steps | Automated in UI testing |
|---|---|---:|---|
| [TC-SYS-01](test-cases/TC-SYS-01.md) | Staff creates a product and a 10% coupon → guest buys 2 with the coupon → staff completes the order → customer sees "Order completed" | 30 | Yes |
| [TC-SYS-02](test-cases/TC-SYS-02.md) | Staff creates a product with stock 3 in Accessories → guest finds it in the category and buys 2 → staff cancels the order, stock returns to 3 → customer sees "Order cancelled" | 26 | Yes |
| [TC-SYS-03](test-cases/TC-SYS-03.md) | Staff creates a product → guest submits a 5-star review (invalid submissions rejected) → staff approves it → review is shown publicly | 19 | Yes |
 
- Traceability matrix: [rtm/RTM.md](rtm/RTM.md)
- Defect reports: [defect-reports/README.md](defect-reports/README.md)
- Screenshots: [screenshots/](screenshots/)
## Folder structure
 
```
System testing/
├── README.md                ← this file: overview + execution summary
├── test-cases/              ← TC-SYS-01.md, TC-SYS-02.md, TC-SYS-03.md
├── rtm/RTM.md               ← requirement traceability matrix
├── defect-reports/          ← README.md (defect list + template), DEF-SYS-XX.md
└── screenshots/
    ├── preparation/
    ├── TC-SYS-01/
    ├── TC-SYS-02/
    └── TC-SYS-03/
```
 
## Preparation (checked before execution)
 
1. The G02 staff account can log in to wp-admin and open Products, Marketing > Coupons, WooCommerce > Orders and Products > Reviews.
2. Cash on delivery is enabled at checkout.
3. The Accessories category exists (used by TC-SYS-02; shared categories are not edited).
4. Product reviews are enabled, guests can review, and reviews from new authors are held for approval (used by TC-SYS-03).
5. No shipping fee is charged, so expected totals equal the cart totals.
Screenshots of these checks are in `screenshots/preparation/`.
 
## Execution rules
 
1. Run ID (`RUNID`) = the date and time of the run, `YYYYMMDD-HHMMSS`. Every product, coupon and email created in a run gets it, so each run uses new data.
2. Staff work in a normal browser window; the customer uses a separate private window (guest, not logged in).
3. The actual result of every step is recorded. A step passes only when it matches the expected result; otherwise it fails. Blocked = could not run because of an earlier failure.
4. Every step has a screenshot: `screenshots/TC-SYS-0X/TC-SYS-0X_StepN_ShortName.png` (`_FAIL` added for a failed step).
5. Every failed step has a defect report.
6. Demo data and data from other groups are never edited or deleted. Only orders created by G02 are completed or cancelled.
## Execution summary
 
| Test case | Executed on | Run ID | Order | Total steps | Passed | Failed | Blocked | Result | Defects |
|---|---|---|---|---:|---:|---:|---:|---|---|
| TC-SYS-01 | 16 Nov 2026, 16:06 | `20261116-160636` | `#507` | 30 | 30 | 0 | 0 | Pass | None |
| TC-SYS-02 | 16 Nov 2026, 19:46 | `20261116-194618` | `#534` | 26 | | | | | |
| TC-SYS-03 | 16 Nov 2026, 21:14 | `20261116-211430` | - | 19 | | | | | |
| **Total** | | | | **75** | | | | | |
 
## Results
 
- **TC-SYS-01:** all 30 steps passed. The coupon discount (฿100.00), stock reduction (10 → 8), coupon usage (0 → 1) and the status change to Completed were correct on both sides.
- **TC-SYS-02:** (fill in after step 8 is re-run) Stock limit, zero-quantity handling, cancellation and stock restoration (3 → 1 → 3) worked as expected.
- **TC-SYS-03:** (fill in after step 11 is resolved) Reviews without a rating were rejected. The review was held for approval, approved by staff and then shown publicly with Reviews (1).