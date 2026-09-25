use super::*;

#[test]
fn doc_routes_are_gated_until_the_env_names_the_feature() {
    assert_eq!(
        disabled_doc_feature_for_route_in("versioning", ""),
        Some("versions")
    );
    assert_eq!(
        disabled_doc_feature_for_route_in("/versioning/", ""),
        Some("versions")
    );
    assert_eq!(disabled_doc_feature_for_route_in("i18n", ""), Some("i18n"));
    for route in ["quickstart", "roadmap", "landing", "guide/versioning"] {
        assert_eq!(
            disabled_doc_feature_for_route_in(route, ""),
            None,
            "{route}"
        );
    }
    assert_eq!(
        disabled_doc_feature_for_route_in("versioning", "versions"),
        None
    );
    assert_eq!(
        disabled_doc_feature_for_route_in("i18n", "versions"),
        Some("i18n")
    );
    assert_eq!(
        disabled_doc_feature_for_route_in("i18n", " i18n , versions "),
        None
    );
    assert_eq!(
        disabled_doc_feature_for_route_in("versioning", " , "),
        Some("versions")
    );
}

#[test]
fn api_module_gate_is_membership_in_the_table_and_covers_submodules() {
    let gates = [("folio_docs.docs.integrations.roadmap", "plugins")];
    assert_eq!(
        disabled_api_feature_for_module_in("folio_docs.docs.integrations.roadmap", &gates, ""),
        Some("plugins")
    );
    assert_eq!(
        disabled_api_feature_for_module_in("folio_docs.docs.integrations.roadmap.data", &gates, ""),
        Some("plugins")
    );
    assert_eq!(
        disabled_api_feature_for_module_in("folio_docs.docs.integrations.roadmapper", &gates, ""),
        None
    );
    assert_eq!(
        disabled_api_feature_for_module_in("folio_docs.docs.integrations.landing", &gates, ""),
        None
    );
    assert_eq!(
        disabled_api_feature_for_module_in(
            "folio_docs.docs.integrations.roadmap",
            &gates,
            "plugins"
        ),
        None
    );
    assert_eq!(
        disabled_api_feature_for_module_in(
            "folio_docs.docs.integrations.roadmap",
            &gates,
            "versions"
        ),
        Some("plugins")
    );
    // This release gates no API module.
    assert!(DISABLED_API_MODULES.is_empty());
    assert_eq!(
        disabled_api_feature_for_module("folio_docs.docs.integrations.roadmap"),
        None
    );
}
