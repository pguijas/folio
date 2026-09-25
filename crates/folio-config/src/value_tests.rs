use super::*;

#[test]
fn quoted_value_spells_scalars_as_the_config_does() {
    let yaml: Value = serde_yaml_ng::from_str(
        "[a, \"it's\", 'say \"hi\"', 42, 1.5, true, false, null, [1, x], {k: v}]",
    )
    .unwrap();
    let items = yaml.as_sequence().unwrap();
    let reprs: Vec<String> = items.iter().map(quoted_value).collect();
    assert_eq!(
        reprs,
        [
            "'a'",
            "'it\\'s'",
            "'say \"hi\"'",
            "42",
            "1.5",
            "true",
            "false",
            "null",
            "[1, 'x']",
            "{'k': 'v'}"
        ]
    );
    assert_eq!(quoted("a\nb\\c"), "'a\\nb\\\\c'");
}

#[test]
fn unknown_keys_warn_once_sorted_with_the_near_key() {
    let mapping: Mapping =
        serde_yaml_ng::from_str("vesion: 1\nname: x\nhomepage: y\n3: z\n").unwrap();
    let mut warnings = Vec::new();
    warn_unknown_keys(&mapping, &["name", "version"], "project", &mut warnings);
    assert_eq!(
        warnings,
        ["Unknown project keys in docs.yaml: 3, homepage, vesion (did you mean 'version'?)"]
    );
    let mut warnings = Vec::new();
    warn_unknown_keys(
        &mapping,
        &["name", "version", "homepage", "vesion", "3"],
        "project",
        &mut warnings,
    );
    assert_eq!(warnings, ["Unknown project keys in docs.yaml: 3"]);
}
