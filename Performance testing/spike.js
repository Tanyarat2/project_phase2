import { shopJourney, withScenarioThresholds } from './common.js';

// Member 5: 1 VU -> abrupt 6-VU spike -> four 30-second recovery windows.
// Each period has separate k6 summary metrics to estimate recovery to normal.
const periods = [
  ['baseline', 1, '45s', '0s'],
  ['spike', 6, '20s', '45s'],
  ['recovery_0_30s', 1, '30s', '65s'],
  ['recovery_30_60s', 1, '30s', '95s'],
  ['recovery_60_90s', 1, '30s', '125s'],
  ['recovery_90_120s', 1, '30s', '155s'],
];
const scenarios = {};
for (const [name, vus, duration, startTime] of periods) {
  scenarios[name] = { executor: 'constant-vus', vus, duration, startTime, gracefulStop: '0s' };
}

export const options = {
  scenarios,
  thresholds: withScenarioThresholds(periods.map((entry) => entry[0])),
};

export default function () {
  shopJourney();
}
