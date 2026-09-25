//! The one list of environment a `folio` test run must not inherit.
//!
//! Shared by every CLI test target through `#[path]`, so a new switch is
//! scrubbed everywhere the day it is added.

use std::process::Command;

/// Variables that would steer a build: Folio's own switches, the colour
/// forcers, and the GitHub Actions outputs the CI-aware commands write to.
pub const SCRUBBED: [&str; 10] = [
    "CI",
    "CLICOLOR_FORCE",
    "COLORTERM",
    "COLUMNS",
    "FOLIO_BASE_PATH",
    "FOLIO_DEPLOY_PROVIDER",
    "FOLIO_EXPERIMENTAL",
    "FOLIO_TEMPLATE_DIR",
    "FOLIO_TRACE",
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
        .env("FOLIO_FRONTEND_RUNTIME", "noop")
}
