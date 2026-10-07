/** Classes module for testing. */

/**
 * A simple calculator.
 */
export class Calculator {
  /** Maximum precision. */
  static MAX_PRECISION = 10;

  /**
   * Create a calculator.
   * @param {number} precision - The precision.
   */
  constructor(precision) {
    this.precision = precision;
  }

  /**
   * Add two numbers.
   * @param {number} a - First number.
   * @param {number} b - Second number.
   * @returns {number} The sum.
   */
  add(a, b) {
    return a + b;
  }

  /**
   * Async multiply.
   * @param {number} a - First number.
   * @param {number} b - Second number.
   * @returns {Promise<number>} The product.
   */
  async multiply(a, b) {
    return a * b;
  }

  /** Get the current precision. */
  get value() {
    return this.precision;
  }

  /** Set the precision. */
  set value(v) {
    this.precision = v;
  }

  /**
   * Create a default calculator.
   * @returns {Calculator} A new calculator.
   */
  static create() {
    return new Calculator(2);
  }
}

/**
 * An event emitter.
 */
export default class EventBus extends EventEmitter {
  /**
   * Emit an event.
   * @param {string} event - The event name.
   */
  emit(event) {
    super.emit(event);
  }
}
