import { shopJourney, thresholds } from './common.js';

// Member 5: one uninterrupted 15-minute run with three tagged five-minute windows.
const timeWindows = ['early', 'middle', 'late'];
const periodThresholds = { ...thresholds };
for (const period of timeWindows) {
  periodThresholds[`http_req_duration{soak_period:${period}}`] = ['p(95)<1000'];
  periodThresholds[`http_req_failed{soak_period:${period}}`] = ['rate<0.02'];
}

export const options = {
  scenarios: {
    soak_2vus: { executor: 'constant-vus', vus: 2, duration: '15m', gracefulStop: '10s' },
  },
  thresholds: periodThresholds,
};

export function setup() {
  return { startedAt: Date.now() };
}

export default function (data) {
  const elapsedMs = Date.now() - data.startedAt;
  const period = elapsedMs < 300000 ? 'early' : elapsedMs < 600000 ? 'middle' : 'late';
  shopJourney({ soak_period: period });
}
