# Performance Testing — ITCS386 Group 02

## 1. Overview

We conducted performance testing on the WooCommerce online shop using **Grafana k6** to evaluate response time, reliability, and system behavior under different workloads.

| Item | Description |
|---|---|
| System Under Test | http://157.85.102.236/shop/ |
| Testing Tool | Grafana k6 |
| Test Types | Average-load, Stress, Soak, Spike |
| Test Dates | 17 and 21 November 2026 |
| Time Zone | Asia/Bangkok (UTC+07:00) |
| Environment | Shared server used by multiple student groups |

Our objective was to evaluate performance under normal traffic, increasing workloads, continuous usage, and sudden traffic spikes.

Because all groups share the same server, we used read-only GET requests without placing orders or modifying shared data.

## 2. Test Design

### 2.1 Customer Journey

All four tests use the same simulated customer journey:

1. **Open Storefront:** Access the online shop homepage.
2. **Browse Products:** Retrieve the product listing.
3. **Search Products:** Search for products by name.
4. **View Product Details:** Retrieve information about a selected product.
5. **Open Product Page:** Access the selected product's page.

A successful journey normally consists of **5 HTTP GET requests and 8 functional checks**.

We also include a random think time of 1.5–2.5 seconds between iterations to simulate pauses between customer activities.

Using the same journey across all four tests allows us to compare how the system performs under different load patterns.

### 2.2 Test Configurations

| Test | Script | Virtual Users | Duration | Objective |
|---|---|---|---|---|
| Average-load | `average_load.js` | 3 VUs | 2 minutes | Measure response time under a small, steady workload |
| Stress | `stress.js` | 1, 2, 3, 5, 7, 10 VUs | 50 seconds per stage, with 10-second boundaries | Identify response-time degradation as workload increases |
| Soak | `soak.js` | 2 VUs | 15 minutes | Observe whether performance deteriorates during continuous use |
| Spike | `spike.js` | 1 → 6 → 1 VUs | 45s → 20s → 120s | Evaluate sudden traffic increases and recovery behavior |

**Configuration rationale**

**Average-load:** We selected 3 VUs to represent a small, constant workload suitable for a shared test environment. Two minutes provides an initial measurement of normal-load performance.

**Stress:** We increased the workload gradually instead of immediately applying 10 VUs. This allows us to compare response times at different concurrency levels and identify where the latency threshold is exceeded. The initial experiment covered 1–5 VUs. The current test expands the range to 7 and 10 VUs based on the initial findings.

**Soak:** We selected 2 VUs for 15 minutes to observe performance under continuous activity without placing excessive sustained load on the shared server. Dividing the results into three five-minute windows allows comparison between the beginning, middle, and end of the test.

**Spike:** We used 1 VU as the baseline, increased to 6 VUs for 20 seconds, and returned to 1 VU for 120 seconds. This design simulates a brief traffic surge followed by an observation period for recovery.

These workload levels were selected for controlled experiments. They are not based on measured production traffic or a verified maximum server capacity.

### 2.3 Performance Thresholds

| Metric | Threshold | Justification |
|---|---|---|
| p95 HTTP Response Time | Less than 1,000 ms | The assignment asks when response time exceeds one second |
| HTTP Error Rate | Less than 2% | Allows a small tolerance for occasional request failures |
| Functional Check Success Rate | Greater than 98% | Ensures that responses contain expected results |
| Failed Customer Journey Rate | Less than 2% | Ensures that most complete customer workflows succeed |

We use the **95th percentile (p95)** rather than average response time because an average can hide slower requests.

For example, a p95 value of 900 ms means approximately 95% of measured requests completed within 900 ms.

The thresholds are experimental acceptance criteria selected for this assignment, not official WooCommerce performance requirements.

## 3. Performance Test Results

### 3.1 Overall Results

| Test | Test Date | Maximum VUs | Overall p95 | HTTP Failures | Result |
|---|---|---:|---:|---:|---|
| Average-load | 17 Nov 2026 | 3 | 1,404.22 ms | 0/460 | Fail — Latency |
| Stress | 21 Nov 2026 | 10 | Approximately 1,070 ms | 0/1,721 | Fail — Latency |
| Soak | 17 Nov 2026 | 2 | 875.79 ms | 2/2,510 (0.08%) | Pass |
| Spike | 17 Nov 2026 | 6 | 1,121.82 ms | 0/370 | Fail — Latency |

The Stress Test result above uses the latest functionally valid run from 21 November 2026.

All four tests were evaluated against the same response-time and HTTP-error thresholds.

### 3.2 Average-load Test

**Configuration:** 3 VUs continuously for 2 minutes.

| Metric | Result |
|---|---:|
| HTTP Requests | 460 |
| HTTP Failures | 0 |
| p95 Response Time | 1,404.22 ms |
| Functional Checks | 736/736 passed |
| Result | Fail — Latency |

All HTTP requests and functional checks succeeded. However, the p95 response time exceeded the one-second threshold.

This indicates that the system experienced slower responses during this particular run, even under a relatively small workload.

Because the server is shared, other groups' activity may have contributed to this result. The exact cause cannot be confirmed without server-side monitoring.

### 3.3 Stress Test

The Stress Test gradually increased concurrent virtual users to investigate when the system begins to exceed the one-second response-time threshold.

The original experiment tested up to 5 VUs. Based on those results, we expanded the experiment to include 7 and 10 VUs.

**Latest functionally valid run — 21 November 2026**

| VUs | p95 Response Time | HTTP Error Rate | Threshold Result |
|---|---:|---:|---|
| 1 | 490.57 ms | 0% | Pass |
| 2 | 474.29 ms | 0% | Pass |
| 3 | 517.11 ms | 0% | Pass |
| 5 | 697.39 ms | 0% | Pass |
| 7 | 974.77 ms | 0% | Pass |
| 10 | Approximately 1,570 ms | 0% | Fail |

**Overall measurements**

| Metric | Result |
|---|---:|
| Total HTTP Requests | 1,721 |
| HTTP Failures | 0 |
| Functional Checks | 2,753/2,753 passed |
| Customer Journey Failure Rate | 0% |
| Overall p95 | Approximately 1,070 ms |
| Highest Passing Tested Load | 7 VUs |
| First Failing Tested Load | 10 VUs |

**Result: Fail — Response Time at 10 VUs**

The results show a general increase in response time as concurrency increases.

At 5 VUs, p95 was 697.39 ms, comfortably below our threshold.

At 7 VUs, p95 reached 974.77 ms, leaving only approximately 25 ms before exceeding the one-second threshold.

At 10 VUs, p95 increased to approximately 1.57 seconds.

Despite the slower responses, all functional checks passed and the HTTP error rate remained at 0%.

This indicates that the observed problem in this run was **response-time degradation rather than HTTP request failure**.

The 10-VU stage stopped after approximately 42 of its planned 50 seconds because the `abortOnFail` threshold condition was triggered. Therefore, the final stage represents a partial-duration measurement.

An earlier Stress run also exceeded the threshold at 7 VUs. This demonstrates that the performance boundary is not completely stable between runs.

We cannot conclude that 7 VUs is the system's guaranteed maximum supported concurrency. We can only conclude that it was the highest tested level meeting the latency requirement in the latest valid run.

### 3.4 Soak Test

**Configuration:** 2 VUs continuously for 15 minutes.

To identify changes over time, we divided the test into three five-minute observation windows.

| Time Window | p95 Response Time | HTTP Error Rate |
|---|---:|---:|
| 0–5 minutes | 909.81 ms | 0% |
| 5–10 minutes | 903.98 ms | Approximately 0.25% (2 requests) |
| 10–15 minutes | 817.21 ms | 0% |

**Overall measurements**

| Metric | Result |
|---|---:|
| Total HTTP Requests | 2,510 |
| HTTP Failures | 2 (0.08%) |
| Overall p95 | 875.79 ms |
| Functional Checks | 4,013/4,016 passed |
| Customer Journeys | 502 |
| Failed Customer Journeys | 1 |

**Result: Pass**

The p95 response time did not progressively increase during the 15-minute test.

The final observation window had a lower p95 than the first window, decreasing from 909.81 ms to 817.21 ms.

Two HTTP requests failed during the middle period, but the overall failure rate remained below our 2% threshold.

These findings suggest that no sustained performance deterioration was observed during the tested period.

However, a 15-minute test is insufficient to establish long-term stability or rule out memory leaks.

### 3.5 Spike Test

**Configuration:** 1 VU for 45 seconds, increased to 6 VUs for 20 seconds, then reduced to 1 VU for 120 seconds.

| Period | VUs | p95 Response Time | HTTP Error Rate |
|---|---:|---:|---:|
| Baseline | 1 | 893.53 ms | 0% |
| Spike | 6 | 1,184.10 ms | 0% |
| Recovery 0–30s | 1 | 565.64 ms | 0% |
| Recovery 30–60s | 1 | 453.67 ms | 0% |
| Recovery 60–90s | 1 | 1,273.77 ms | 0% |
| Recovery 90–120s | 1 | 1,447.58 ms | 0% |

**Overall measurements**

| Metric | Result |
|---|---:|
| Total HTTP Requests | 370 |
| HTTP Failures | 0 |
| Overall p95 | 1,121.82 ms |
| Functional Checks | 594/594 passed |

**Result: Fail — Latency**

During the spike, p95 increased from 893.53 ms to 1,184.10 ms, exceeding the one-second threshold.

After the workload decreased to 1 VU, p95 initially improved to below one second.

However, during the later recovery windows, response time increased above the threshold again.

Therefore, **stable recovery could not be confirmed within the 120-second observation period**.

The test also reported 11 interrupted iterations at scenario boundaries due to `gracefulStop: '0s'`. These interruptions are separate from HTTP request failures.

## 4. Answers to the Assignment Questions

### Q1. How many virtual users can the system serve before response time exceeds one second?

In the latest functionally valid Stress Test, the system maintained a p95 response time below one second through **7 VUs**, with a measured p95 of 974.77 ms.

At 10 VUs, p95 increased to approximately 1.57 seconds and exceeded the threshold.

Therefore, **7 VUs was the highest tested workload that passed the latency requirement in the latest run**.

However, the exact boundary between 7 and 10 VUs remains unknown because 8 and 9 VUs were not tested.

Additionally, an earlier run exceeded the threshold at 7 VUs, suggesting performance variability between runs.

These results do not establish the system's absolute maximum capacity.

### Q2. At how many virtual users does the system start to show problems in the Stress Test?

The latest valid run first exceeded the one-second p95 threshold at **10 VUs**.

At this level, p95 reached approximately 1.57 seconds, while HTTP failures remained at 0%.

This suggests that response-time degradation appeared before HTTP request failures.

However, another run exceeded the threshold at 7 VUs. Therefore, the observed degradation occurs around the tested 7–10 VU range under different run conditions, rather than at a proven fixed limit.

### Q3. In the Soak Test, do response time or error rate get worse over time?

No consistent deterioration was observed during the 15-minute Soak Test.

The p95 response time decreased from 909.81 ms during the first five minutes to 817.21 ms during the final five minutes.

Two HTTP errors occurred during the middle observation window, but no HTTP failures occurred during the final window.

Therefore, the results do not show progressive performance degradation during the tested period.

### Q4. In the Spike Test, how long does the system take to return to normal service?

The system initially returned below the one-second p95 threshold during the first 30-second recovery window.

However, p95 increased above one second again after 60 seconds.

Therefore, stable recovery could not be confirmed within the full 120-second observation period.

We cannot report a definite recovery time from this run.

### Q5. What do `http_req_failed`, `http_req_duration`, and `vus_max` tell us?

**`http_req_failed` — HTTP Request Failure Rate**

Measures the proportion of HTTP requests classified as failed.

| Test | HTTP Failure Rate |
|---|---:|
| Average-load | 0% |
| Stress (latest valid run) | 0% |
| Soak | Approximately 0.08% |
| Spike | 0% |

Low HTTP failure rates indicate that requests generally completed successfully at the HTTP level. However, this metric alone does not guarantee that the returned content is correct.

**`http_req_duration` — HTTP Response Time**

Measures the time taken for HTTP requests, excluding initial connection establishment.

We evaluated the 95th percentile against our one-second threshold.

Average-load, Stress, and Spike exceeded the threshold in their selected main runs, while Soak remained below it.

**`vus_max` — Maximum Allocated Virtual Users**

Represents the maximum number of virtual users allocated by k6 during a test.

| Test | `vus_max` |
|---|---:|
| Average-load | 3 |
| Stress | 10 |
| Soak | 2 |
| Spike | 6 |

This metric describes the configured testing capacity, not the maximum capacity the server can handle.

For additional validation, we used functional checks and the `shop_flow_failed` metric to identify customer journeys that did not complete correctly.

## 5. Test History and Reliability

Because the server is shared, we recorded the dates and times of each test and retained the original k6 summaries.

### 5.1 Initial Test Runs — 17 November 2026

| Test | Start Time (UTC+7) | Evidence Directory |
|---|---|---|
| Average-load | 21:26:53 | `results/average_20261117_212653/` |
| Stress | Approximately 22:33:50 | `results/stress_20261117_223350/` |
| Soak | 22:45:39 | `results/soak_20261117_224539/` |
| Spike | 23:02:18 | `results/spike_20261117_230217/` |

The original Stress Test covered 1, 2, 3, and 5 VUs.

| VUs | Original p95 |
|---|---:|
| 1 | 438.12 ms |
| 2 | 503.76 ms |
| 3 | 550.29 ms |
| 5 | 806.28 ms |

All tested levels passed the latency threshold.

However, the test did not reach a failing workload, so it could not determine where the system started exceeding one second.

We therefore expanded the Stress Test to cover higher concurrency levels.

### 5.2 Additional Stress Runs — 21 November 2026

| Run Time (UTC+7) | Observation |
|---|---|
| 16:15 | Completed 1–5 VU stages; all tested latency thresholds passed |
| 16:23 | p95 reached approximately 1.03 seconds at 7 VUs, triggering early termination |
| 16:31 | 672 of 691 customer journeys failed functional validation despite a 0% HTTP error rate |
| 16:45 | Functionally valid run; 7 VUs passed, while 10 VUs exceeded the latency threshold |

The 16:31 run produced unusually low response times of approximately 20 ms for several load levels.

However, the product-listing validation failed for most customer journeys. Therefore, these response times cannot be interpreted as successful full-customer-journey performance.

A subsequent single-VU diagnostic successfully retrieved six products with HTTP 200 and no observed redirect. This confirmed that the API responded correctly during the diagnostic but did not establish the cause of the earlier failures.

Possible contributing factors include changing server conditions or concurrent testing activity, but no specific cause has been confirmed.

All available test results are retained as evidence, including failed and abnormal runs, to avoid selectively reporting only favorable measurements.

## 6. Limitations

Our experiment has several limitations:

- **Shared environment:** Other student groups used the same server, and their activity may have influenced response times.
- **Limited workload range:** We tested selected VU levels rather than every possible concurrency level.
- **Partial Stress stage:** The latest 10-VU stage stopped early after exceeding the latency threshold.
- **Limited Soak duration:** Fifteen minutes cannot establish long-term reliability.
- **Unknown production traffic:** We did not have actual customer traffic data to validate the representativeness of our workloads.
- **Between-run variability:** Different runs produced different response times and functional outcomes.
- **Limited server visibility:** We did not have CPU, memory, database, or other server-side measurements to identify the root causes of performance degradation.

These limitations mean that the results describe the system's behavior under our tested conditions, not its guaranteed production capacity.

## 7. Conclusion

Our performance testing identified several important findings.

The **Average-load Test** exceeded the one-second response-time threshold at 3 VUs during its original run.

The **Stress Test** showed increasing response times as concurrency increased. In the latest valid run, 7 VUs remained below the threshold with a p95 of 974.77 ms, while 10 VUs exceeded the threshold with a p95 of approximately 1.57 seconds.

The **Soak Test** did not show progressive performance deterioration over 15 minutes.

The **Spike Test** demonstrated that latency increased during sudden traffic and that stable recovery could not be confirmed within 120 seconds.

Overall, HTTP request failures were rare, but response-time degradation occurred under several workload conditions.

**Our main finding is that successful HTTP requests do not necessarily imply acceptable response time or a successful customer journey.** Both performance metrics and functional checks are necessary to evaluate system behavior accurately.

## 8. Execution and Evidence

### 8.1 Running the Tests

From the `Performance testing` directory, run:

- Average-load: `k6 run .\average_load.js`
- Stress: `k6 run .\stress.js`
- Soak: `k6 run .\soak.js`
- Spike: `k6 run .\spike.js`

Only run load tests during an approved testing window because the server is shared.

### 8.2 Saving a k6 Summary

For example, to save a new Stress Test summary in PowerShell:

```powershell
$runDir = ".\results\stress_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz" |
    Set-Content "$runDir\run_time_local.txt"

k6 run --summary-export "$runDir\summary.json" .\stress.js
```

### 8.3 Evidence Files

All original k6 summaries and recorded run timestamps are stored in the `results/` directory.

The latest functionally valid Stress Test summary is located at:

`results/stress10_20261121_164507/summary.json`

The original Stress Test script from 17 November is also preserved in its historical results directory to maintain reproducibility.

Later runs are documented separately rather than replacing or modifying earlier measurements.
