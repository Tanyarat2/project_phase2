"""Turn a genuine k6 stress summary into a per-stage table; never invent missing levels."""
from pathlib import Path
import json
import math
import sys

LEVELS = [1, 2, 3, 5, 7, 10]


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def describe(path):
    obj = json.loads(path.read_text(encoding='utf-8-sig'))
    metrics = obj.get('metrics', {})
    tm = path.parent / 'run_time_local.txt'
    when = tm.read_text(encoding='utf-8-sig').strip() if tm.exists() else 'Not recorded'
    rows = []
    for vu in LEVELS:
        key = f'stress_{vu}vus'
        resp = metrics.get(f'http_req_duration{{scenario:{key}}}', {})
        err = metrics.get(f'http_req_failed{{scenario:{key}}}', {})
        p95, er = number(resp.get('p(95)')), number(err.get('value'))
        if p95 is None:
            rows.append((vu, None, None, 'Not run / no measurements'))
        elif er is None:
            rows.append((vu, p95, None, 'Error rate unavailable'))
        else:
            result = 'PASS' if p95 < 1000 and er < 0.02 else 'FAIL'
            rows.append((vu, p95, er, result))
    lines = [
        '# New Stress Test - observed results', '',
        f'- Local start time: {when}',
        '- Thresholds: p95 response time < 1000 ms, HTTP error rate < 2%.',
        '- The requested workload is 1, 2, 3, 5, 7, 10 VUs; stages after an early stop are **not tested**.',
        '- Same read-only shopping journey as the earlier runs.', '',
        '| VUs | p95 (ms) | HTTP failures (%) | Stage result |',
        '| ---: | ---: | ---: | :--- |',
    ]
    for vu, p95, er, label in rows:
        lines.append(f'| {vu} | {p95:.2f} | {er*100:.2f} | {label} |' if p95 is not None and er is not None else
                     f'| {vu} | {f"{p95:.2f}" if p95 is not None else "-"} | - | {label} |')
    measured = [(vu, p95, er, label) for vu, p95, er, label in rows if p95 is not None and er is not None]
    fails = [(vu, p95, er) for vu, p95, er, label in measured if label == 'FAIL']
    lines += ['', '## Assignment Q1 and Q2 (this run only)', '']
    if fails:
        vu, p95, er = fails[0]
        passed = [x for x in measured if x[0] < vu and x[3] == 'PASS']
        prior = passed[-1][0] if passed else None
        reason = []
        if p95 >= 1000: reason.append('p95 >= 1000 ms')
        if er >= 0.02: reason.append('HTTP failures >= 2%')
        lines.append(f'The **first tested stage** that failed either threshold in this run was **{vu} VUs** ({", ".join(reason)}).')
        if prior is not None: lines.append(f'The last earlier passing tested stage was **{prior} VUs**. The exact crossing between tested levels was not measured.')
    elif measured:
        lines.append(f'All measured stages through **{measured[-1][0]} VUs** passed both criteria. The failure point was not identified.')
    else:
        lines.append('No valid stage metrics: cannot answer based on this run.')
    lines += [
        '',
        '**Do not claim maximum server capacity.** This is a single test on a shared server.',
        'An early stop may have occurred; check console.txt, and do not mark missing stages as Pass.',
        'The 2026-11-17 Average-load result at 3 VUs failed p95, while the historical stress result at 3 VUs passed: record both without concealing the difference.',
        'Threshold booleans in k6 --summary-export indicate threshold breaches (true = breached), not success.',
        ''
    ]
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: py analyze_stress.py results/stress_YYYYMMDD_HHMMSS/summary.json')
    p = Path(sys.argv[1])
    if not p.is_file():
        raise SystemExit(f'Not found: {p}')
    output = describe(p)
    dest = p.with_name('analysis.md')
    dest.write_text(output, encoding='utf-8')
    print(output)
    print(f'Saved: {dest}')
