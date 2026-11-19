import { shopJourney, thresholds } from './common.js';

// Member 4: normal customer traffic, 3 concurrent visitors for 2 minutes.
export const options = {
  scenarios: {
    average_3vus: { executor: 'constant-vus', vus: 3, duration: '2m', gracefulStop: '10s' },
  },
  thresholds,
};

export default function () {
  shopJourney();
}
