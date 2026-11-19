import { shopJourney, thresholds } from './common.js';

// Safe short demonstration before any full load tests.
export const options = { vus: 1, duration: '20s', thresholds };

export default function () {
  shopJourney();
}
