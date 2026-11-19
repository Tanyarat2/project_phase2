import { shopJourney, withScenarioThresholds } from './common.js';

// Member 4: find the first response-time problem near the observed 1-3 VU range.
// Ten-second boundaries let the previous users finish before the next level.
const levels = [1, 2, 3, 5];
const scenarios = {};
levels.forEach((vus, index) => {
  scenarios[`stress_${vus}vus`] = {
    executor: 'constant-vus',
    vus,
    duration: '50s',
    startTime: `${index * 60}s`,
    gracefulStop: '10s',
  };
});

export const options = {
  scenarios,
  thresholds: withScenarioThresholds(levels.map((vus) => `stress_${vus}vus`)),
};

export default function () {
  shopJourney();
}
