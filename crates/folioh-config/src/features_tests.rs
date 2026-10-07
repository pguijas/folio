use super::*;

#[test]
fn disabled_features_need_the_env_var() {
    assert!(!is_feature_enabled_in("i18n", ""));
    assert!(!is_feature_enabled_in("versions", ""));
    assert!(is_feature_enabled_in("i18n", "i18n"));
    assert!(is_feature_enabled_in("versions", " i18n , versions ,, "));
    assert!(!is_feature_enabled_in("versions", "i18n"));
}

#[test]
fn features_outside_the_disabled_set_are_always_on() {
    assert!(is_feature_enabled_in("search", ""));
    assert!(is_feature_enabled_in("landing", "versions"));
}

#[test]
fn state_is_disabled_or_the_sorted_csv() {
    assert_eq!(experimental_feature_state_in(""), "disabled");
    assert_eq!(experimental_feature_state_in(" , "), "disabled");
    assert_eq!(
        experimental_feature_state_in("versions, i18n"),
        "i18n,versions"
    );
    assert_eq!(experimental_feature_state_in("b,a,b"), "a,b");
}

#[test]
fn disabled_feature_message_names_the_feature() {
    assert_eq!(
        disabled_feature_message("i18n"),
        "The 'i18n' feature is not available in this release."
    );
}
