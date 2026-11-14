// Stand-in for 'k6/metrics': custom metrics keep every sample.
class Metric {
  constructor(name, type) {
    this.samples = [];
    globalThis.__K6.metrics[name] = { type, samples: this.samples };
  }
  add(value) { this.samples.push(value); }
}
export class Trend extends Metric { constructor(name) { super(name, 'trend'); } }
export class Rate extends Metric { constructor(name) { super(name, 'rate'); } }
export class Counter extends Metric { constructor(name) { super(name, 'counter'); } }
