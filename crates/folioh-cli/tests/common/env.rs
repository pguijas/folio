//! The one list of environment a `folioh` test run must not inherit.
//!
//! Shared by every CLI test target through `#[path]`, so a new switch is
//! scrubbed everywhere the day it is added.

use std::process::Command;

/// Variables that would steer a build: Folioh's own switches, the colour
/// forcers, and the GitHub Actions outputs the CI-aware commands write to.
pub const SCRUBBED: [&str; 10] = [
    "CI",
    "CLICOLOR_FORCE",
    "COLORTERM",
    "COLUMNS",
    "FOLIOH_BASE_PATH",
    "FOLIOH_DEPLOY_PROVIDER",
    "FOLIOH_EXPERIMENTAL",
    "FOLIOH_TEMPLATE_DIR",
    "FOLIOH_TRACE",
    "FORCE_COLOR",
];

/// Clear [`SCRUBBED`] and the GitHub Actions sinks, then pin colours off and
/// the no-op frontend runtime. Callers set what they need on top.
pub fn scrub(cmd: &mut Command) -> &mut Command {
    for var in SCRUBBED {
        cmd.env_remove(var);
    }
    cmd.env_remove("GITHUB_OUTPUT")
        .env_remove("GITHUB_STEP_SUMMARY")
        .env("NO_COLOR", "1")
        .env("FOLIOH_FRONTEND_RUNTIME", "noop")
}
