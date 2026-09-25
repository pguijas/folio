/** Greeting utilities. */

/**
 * Greet someone by name.
 * @param {string} name - The person to greet.
 * @param {boolean} [loud=false] - Whether to shout.
 * @returns {string} A greeting message.
 * @example
 * greet("world")
 */
export function greet(name, loud = false) {
  const msg = `Hello, ${name}!`;
  return loud ? msg.toUpperCase() : msg;
}

/** The default greeting. */
export const DEFAULT_GREETING = "Hello!";
