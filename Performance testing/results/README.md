# Measured performance runs

The historical runs below were executed 17 November 2026 (Asia/Bangkok UTC+7). Files containing real metrics are preserved unchanged. The Stress output originally supplied only its `summary.json`; do not invent a missing `console.txt`.

- `average_20261117_212653`: Original Average-load, `summary.json`, `console.txt`, timestamps.
- `stress_20261117_223350`: Original Stress 1,2,3,5 VUs, genuine `summary.json`, and exact `stress_script_used_20261117.js` plus its `common.js` dependency for reproducibility.
- `soak_20261117_224539`: Original Soak, `summary.json`, `console.txt`, timestamps.
- `spike_20261117_230217`: Original Spike, `summary.json`, `console.txt`, timestamps.

New approved stress runs use `stress_YYYYMMDD_HHMMSS` folders and may include `analysis.md`. Never overwrite a historical run or label an untested stage as passed.
