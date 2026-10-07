use std::path::Path;

use serde_yaml_ng::{Mapping, Value};

use super::{parse_docs_config_with, DocsConfig};
use crate::error::ConfigError;

pub(crate) fn mapping(yaml: &str) -> Mapping {
    match serde_yaml_ng::from_str::<Value>(yaml).expect("test yaml parses") {
        Value::Null => Mapping::new(),
        Value::Mapping(m) => m,
        other => panic!("test yaml is not a mapping: {other:?}"),
    }
}

/// Parse in memory against the fake project dir `/proj`.
pub(crate) fn parse_yaml_with(
    yaml: &str,
    experimental: &str,
) -> Result<(DocsConfig, Vec<String>), ConfigError> {
    let mut warnings = Vec::new();
    let config = parse_docs_config_with(
        &mapping(yaml),
        Path::new("/proj"),
        experimental,
        &mut warnings,
    )?;
    Ok((config, warnings))
}

pub(crate) fn parse_yaml(yaml: &str) -> Result<(DocsConfig, Vec<String>), ConfigError> {
    parse_yaml_with(yaml, "")
}

pub(crate) fn parse_ok(yaml: &str) -> DocsConfig {
    let (config, warnings) = parse_yaml(yaml).expect("config parses");
    assert_eq!(warnings, Vec::<String>::new(), "unexpected warnings");
    config
}

pub(crate) fn parse_err(yaml: &str) -> String {
    parse_yaml(yaml)
        .expect_err("config is rejected")
        .to_string()
}
