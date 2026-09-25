/** Math utilities. */

/**
 * A basic calculator.
 */
export class Calculator {
  /**
   * Create a calculator.
   * @param {number} precision - Decimal places.
   */
  constructor(precision) {
    this.precision = precision;
  }

  /**
   * Add two numbers.
   * @param {number} a - First operand.
   * @param {number} b - Second operand.
   * @returns {number} The sum.
   */
  add(a, b) {
    return +(a + b).toFixed(this.precision);
  }
}
