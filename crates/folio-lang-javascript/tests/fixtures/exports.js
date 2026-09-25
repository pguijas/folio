/** Exports module demonstrating various export styles. */

function internal() {}

export { internal };
export { helpers } from "./helpers";
export * from "./utils";

export default function main() {
  return "main";
}
