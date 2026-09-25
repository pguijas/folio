//! The built-in seam of Folio Docs and the three compiled-in built-ins.
//!
//! Owns the `Plugin` trait and its host, the `ExtensionRegistry`, the builtin
//! component manifest and its drift guards, the MDX/authoring contract model,
//! and the landing, roadmap and openapi built-ins. Returns documents, data
//! modules and views as data; `folio-site` writes them. Never prints.

pub mod builder;
pub mod builtins;
pub mod config_components;
pub mod contract;
pub mod drift;
pub mod error;
pub mod hook;
pub mod host;
pub mod jsscan;
pub mod landing;
pub mod landing_page;
pub mod meta;
pub mod msgfmt;
pub mod openapi;
pub mod registry;
pub mod roadmap;
// The test doubles are off in a shipped build, and always on for this
// crate's own tests; no other crate enables the feature today.
#[cfg(any(test, feature = "testing"))]
pub mod testing;

pub use error::{PluginError, PluginsError};
pub use registry::{
    is_js_identifier, ComponentDefinition, ComponentOrigin, DataModuleDefinition,
    ExtensionRegistry, LayoutDefinition, ViewBlock, ViewDefinition,
};

/// The warnings a call collects, in emission order; the binary prints them.
pub type Diagnostics = Vec<String>;

pub use builder::AssetBuilder;
pub use builtins::{
    register_builtin_components, register_builtin_extensions, BUILTIN_COMPONENTS, PUBLIC_LAYOUT,
};
pub use config_components::{component_name_from_stem, register_config_components};
pub use contract::{
    build_authoring_contract, build_contract, contract_config_keys, render_authoring_contract,
    render_mdx_contract_module, required_component_names, validate_template_mdx_contract,
    AuthoringContract, ContractComponent, AUTHORING_CONTRACT_INSTRUCTIONS,
    FOLIO_AUTHORING_CONTRACT_PATH, FOLIO_MDX_CONTRACT_VERSION,
};
pub use hook::{ChangeKind, Plugin, PluginDocument};
pub use host::{build_registry, check_route_collisions, PluginHost};
pub use jsscan::{
    has_component_entry, import_statements, strip_import_statements, strip_js_comments,
};
pub use landing::{normalize_landing, Landing, LandingPlugin};
pub use landing_page::{default_features, LandingPageData};
pub use meta::{merge_meta_entry, write_route_meta};
pub use openapi::{normalize_openapi, OpenApiPlugin, OpenApiSource, Operation};
pub use roadmap::{active_roadmap, get_phases, normalize_roadmap, Roadmap, RoadmapPlugin};
