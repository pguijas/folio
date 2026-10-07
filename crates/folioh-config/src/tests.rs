#[test]
fn known_keys_are_core_then_builtins() {
    let keys = super::known_config_keys();
    assert_eq!(keys.len(), 18);
    assert_eq!(keys[0], "project");
    assert_eq!(&keys[15..], ["landing", "roadmap", "openapi"]);
}
