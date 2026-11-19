# Performance Testing - ITCS386 Group 02

We tested the WooCommerce shop at `http://157.85.102.236/shop/` using **k6**.

## Test design

Each virtual user opens the shop, browses products, searches by product name,
views product details and pauses for 1.5-2.5 seconds. The scripts use public
GET requests only. No orders or data changes are made because all groups share
the server.

Thresholds used in all four tests:

- **p95 response time < 1000 ms**: the assignment asks when responses exceed 1 second.
- **HTTP error rate < 2%**: our tolerance for occasional errors on the shared server.
- Additional checks: functional checks > 98% and failed customer journeys < 2%.

| Test | Script | VUs and duration | Goal |
| --- | --- | --- | --- |
| Average-load | `average_load.js` | 3 VUs, 2 min | Measure normal-load response time |
| Stress | `stress.js` | 1, 2, 3, 5 VUs; 50 sec each, 10-sec boundaries | Find where latency starts to fail |
| Soak | `soak.js` | 2 VUs, 15 min | Check performance over time |
| Spike | `spike.js` | 1 VU (45 sec) -> 6 VUs (20 sec) -> 1 VU (120 sec) | Measure recovery after sudden load |


## Actual results

All tests were run on **17 November 2026 (Asia/Bangkok, UTC+07:00)**.
The numbers below come from the original k6 summary files in `results/`.

| Test | Start time | `vus_max` | Overall p95 | HTTP failures | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Average-load | 21:26:53 | 3 | 1404.22 ms | 0/460 | Fail: latency |
| Stress | about 22:33:50 | 5 | 622.76 ms | 0/855 | Pass |
| Soak | 22:45:39 | 2 | 875.79 ms | 2/2510 (0.08%) | Pass |
| Spike | 23:02:18 | 6 | 1121.82 ms | 0/370 | Fail: latency |

Average-load: All 460 requests and 736 functional checks succeeded, but p95
exceeded our one-second target at 3 VUs.

### Stress details

| VUs | p95 | HTTP errors | Threshold |
| --- | ---: | ---: | --- |
| 1 | 438.12 ms | 0% | Pass |
| 2 | 503.76 ms | 0% | Pass |
| 3 | 550.29 ms | 0% | Pass |
| 5 | 806.28 ms | 0% | Pass |

All 855 requests and 1368 checks succeeded. p95 increased as VUs increased,
but no tested stress level crossed the threshold.

### Soak details

| Time window | p95 | HTTP errors |
| --- | ---: | ---: |
| 0-5 min | 909.81 ms | 0% |
| 5-10 min | 903.98 ms | 0.25% (2 requests) |
| 10-15 min | 817.21 ms | 0% |

The test completed 502 customer journeys. One journey had errors in the middle
period. Overall, 4013/4016 checks passed. Response time did not progressively
worsen during the 15 minutes; the final p95 was lower than the initial p95.

### Spike details

| Period | VUs | p95 | HTTP errors |
| --- | ---: | ---: | ---: |
| Baseline | 1 | 893.53 ms | 0% |
| Spike | 6 | 1184.10 ms | 0% |
| Recovery 0-30 sec | 1 | 565.64 ms | 0% |
| Recovery 30-60 sec | 1 | 453.67 ms | 0% |
| Recovery 60-90 sec | 1 | 1273.77 ms | 0% |
| Recovery 90-120 sec | 1 | 1447.58 ms | 0% |

All 370 HTTP requests and 594 checks succeeded. Latency dropped below one
second in the first recovery window but exceeded the threshold again after
60 seconds. The run had 11 interrupted iterations at scenario boundaries
(`gracefulStop: '0s'`); these are not HTTP failures.

## Answers to the assignment questions

1. **How many VUs before response time exceeds 1 second?** In the stress run,
   p95 remained below 1 second through **5 VUs**. The actual limit was not
   found. This refers to p95; some individual requests took over a second.
2. **When did the stress test start showing problems?** No threshold violation
   occurred at 1, 2, 3 or 5 VUs. The failure point was not reached in this run.
3. **Did soak performance get worse over time?** No progressive slowdown was
   observed. p95 decreased from 909.81 to 817.21 ms. Two HTTP requests failed
   in the middle period, but the last period had zero HTTP errors.
4. **How long did recovery take after the spike?** p95 initially recovered
   within 30 seconds, but rose above 1 second again after 60 seconds. Stable
   recovery was **not confirmed within the 120-second observation period**.
5. **What do the k6 metrics mean?** `http_req_failed` is the HTTP request
   failure rate (0%, 0%, 0.08%, 0% across the four tests).
   `http_req_duration` measures response time; its p95 passed in Stress and
   Soak but failed in Average-load and Spike. `vus_max` is the maximum number
   of VUs allocated by k6 (3, 5, 2, 6), **not** proven server capacity.

