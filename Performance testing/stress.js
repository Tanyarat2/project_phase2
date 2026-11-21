import { shopJourney, withScenarioThresholds } from './common.js';

// Member 4: extended, controlled stress test. This is a NEW design (max 10 VUs).
// The original 1,2,3,5 VU script is archived with its 2026-11-17 results.
// Run ONLY after 10 VUs are approved for the shared course server.
// Stop early if a tested stage breaches response time or HTTP failure criteria.
const levels = [1, 2, 3, 5, 7, 10];
const scenarios = {};

levels.forEach((vus, index) => {
  scenarios[`stress_${vus}vus`] = {
    executor: 'constant-vus',
    vus,
    startTime: `${index * 60}s`,
    duration: '50s',
    gracefulStop: '10s',
  };
});

const thresholds = withScenarioThresholds(levels.map(vus => `stress_${vus}vus`));
levels.forEach((vus, index) => {
  const name = `stress_${vus}vus`;
  // delayAbortEval is relative to the START of the whole test, not the stage.
  // Allow 40 seconds of data at each stage before any automatic early stop.
  const after = `${index * 60 + 40}s`;
  thresholds[`http_req_duration{scenario:${name}}`] = [{
    threshold: 'p(95)<1000', abortOnFail: true, delayAbortEval: after,
  }];
  thresholds[`http_req_failed{scenario:${name}}`] = [{
    threshold: 'rate<0.02', abortOnFail: true, delayAbortEval: after,
  }];
});

export const options = { scenarios, thresholds };
export default function () {
  shopJourney();
}
