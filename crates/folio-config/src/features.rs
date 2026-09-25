//! The `FOLIO_EXPERIMENTAL` gate over release-disabled features.

use std::collections::BTreeSet;

/// Comma-separated feature names that switch disabled features on.
pub const EXPERIMENTAL_ENV_VAR: &str = "FOLIO_EXPERIMENTAL";
/// Features that are off unless named in `FOLIO_EXPERIMENTAL`.
pub const DISABLED_FEATURES: [&str; 2] = ["i18n", "versions"];

fn enabled_set(experimental: &str) -> BTreeSet<&str> {
    experimental
        .split(',')
        .map(str::trim)
        .filter(|part| !part.is_empty())
        .collect()
}

fn env_value() -> String {
    std::env::var(EXPERIMENTAL_ENV_VAR).unwrap_or_default()
}

/// `is_feature_enabled` against an explicit `FOLIO_EXPERIMENTAL` value.
pub fn is_feature_enabled_in(feature: &str, experimental: &str) -> bool {
    !DISABLED_FEATURES.contains(&feature) || enabled_set(experimental).contains(feature)
}

/// Whether `feature` may run: always for features outside `DISABLED_FEATURES`,
/// otherwise only when `FOLIO_EXPERIMENTAL` names it.
pub fn is_feature_enabled(feature: &str) -> bool {
    is_feature_enabled_in(feature, &env_value())
}

/// `experimental_feature_state` against an explicit `FOLIO_EXPERIMENTAL` value.
pub fn experimental_feature_state_in(experimental: &str) -> String {
    let enabled = enabled_set(experimental);
    if enabled.is_empty() {
        return "disabled".to_string();
    }
    enabled.into_iter().collect::<Vec<_>>().join(",")
}

/// `"disabled"` or the sorted, comma-joined enabled feature names (build context).
pub fn experimental_feature_state() -> String {
    experimental_feature_state_in(&env_value())
}

/// The notice a gated surface shows.
pub fn disabled_feature_message(feature: &str) -> String {
    format!("The '{feature}' feature is not available in this release.")
}

#[cfg(test)]
#[path = "features_tests.rs"]
mod tests;
