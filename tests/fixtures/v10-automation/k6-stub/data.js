// Stand-in for 'k6/data': SharedArray is just the array the callback returns.
export class SharedArray {
  constructor(name, fn) { return fn(); }
}
