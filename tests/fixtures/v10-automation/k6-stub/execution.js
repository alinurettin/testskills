// Stand-in for 'k6/execution'.
export default {
  scenario: {
    get startTime() { return globalThis.__K6.scenarioStart; },
    get iterationInTest() { return globalThis.__K6.iteration; },
  },
  vu: { get idInTest() { return globalThis.__K6.vu; } },
  test: {
    abort(message) {
      globalThis.__K6.aborted = message;
      throw new Error(`aborted: ${message}`);
    },
  },
};
