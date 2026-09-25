//! `PluginsError`: every failure this crate raises; `Display` is the exact
//! user-facing sentence.

use std::path::PathBuf;

use crate::registry::ComponentOrigin;

/// What a plugin hook returns on failure: any error, boxed.
pub type PluginError = Box<dyn std::error::Error + Send + Sync>;

/// One error enum for the crate; the CLI prints `Build failed: {message}`.
#[derive(Debug, thiserror::Error)]
pub enum PluginsError {
    /// A fail-fast hook raised; names the plugin, the hook and the cause.
    #[error("Plugin '{plugin_label}' failed in hook '{hook_name}': {source}")]
    Hook {
        plugin_label: String,
        hook_name: &'static str,
        #[source]
        source: PluginError,
    },
    /// A name that is not a JS identifier (`component name`, `layout slot`, ...).
    #[error("Invalid {label}: {value}")]
    InvalidIdentifier { label: &'static str, value: String },
    #[error(
        "Component already registered: {name} (existing origin: {existing}; new origin: {new})"
    )]
    ComponentRegistered {
        name: String,
        existing: ComponentOrigin,
        new: ComponentOrigin,
    },
    #[error("Layout already registered: {0}")]
    LayoutRegistered(String),
    #[error("Layout must define at least one slot")]
    LayoutWithoutSlots,
    #[error("Data module already registered: {0}")]
    DataModuleRegistered(String),
    #[error("View path already registered: {0}")]
    ViewRegistered(String),
    #[error("Unknown layout for view {path}: {layout}")]
    UnknownLayout { path: String, layout: String },
    #[error("Unknown slot for layout {layout}: {slot}")]
    UnknownSlot { layout: String, slot: String },
    #[error("Unknown component for view {path}: {component}")]
    UnknownComponent { path: String, component: String },
    #[error("Component directory not found: {}", .0.display())]
    ComponentDirNotFound(PathBuf),
    #[error("Cannot derive a component name from file: {}", .0.display())]
    ComponentNameFromFile(PathBuf),
    #[error("Component specs require string 'name' and 'from' fields")]
    ComponentSpecFields,
    #[error("Component export must be a string: {0}")]
    ComponentExport(String),
    #[error("Plugin document route must be a clean relative URL: {0}")]
    DocumentRoute(String),
    #[error("PluginDocument.source must be a path ending in .md or .mdx")]
    DocumentSuffix,
    #[error("Plugin document source not found: {}", .0.display())]
    DocumentSourceMissing(PathBuf),
    /// Reading or parsing a collected document.
    #[error(transparent)]
    Markdown(#[from] folio_mdx::MdxError),
    #[error("Documentation route collision at public route {public}: {previous_route} ({previous_owner}) and {route} ({owner})")]
    RouteCollision {
        public: String,
        previous_route: String,
        previous_owner: String,
        route: String,
        owner: String,
    },
    #[error("openapi source {label}: spec file not found at '{}' (path '{raw_path}' resolved against project directory '{}')", .path.display(), .project_dir.display())]
    OpenApiSpecNotFound {
        label: String,
        path: PathBuf,
        raw_path: String,
        project_dir: PathBuf,
    },
    /// A `roadmap:` entry the renderer cannot read.
    #[error("{path} must be {expected} (got {got})")]
    RoadmapShape {
        path: String,
        expected: &'static str,
        got: &'static str,
    },
    /// A required roadmap phase or feature field that is absent.
    #[error("{path} is missing; {needs}")]
    RoadmapMissing { path: String, needs: &'static str },
    /// A key the roadmap phase or feature type does not declare.
    #[error("{path}.{key} is not a {entry} key{hint}; a {entry} takes {known}")]
    RoadmapUnknownKey {
        path: String,
        key: String,
        entry: &'static str,
        hint: String,
        known: &'static str,
    },
    /// A phase `status` outside the four the renderer draws.
    #[error("{path} must be one of 'shipped', 'active', 'next', 'later'; got {got}{hint}")]
    RoadmapStatus {
        path: String,
        got: String,
        hint: String,
    },
    /// A spec `path` that resolves outside the project directory.
    #[error("openapi source {label}: spec path '{raw_path}' must stay within the project directory '{}'", .project_dir.display())]
    OpenApiSpecOutsideProject {
        label: String,
        raw_path: String,
        project_dir: PathBuf,
    },
    /// A configured `route` with a `.` or `..` segment.
    #[error("openapi source {label}: route '{route}' must not contain '.' or '..' segments")]
    OpenApiRoute { label: String, route: String },
    /// An OpenAPI spec (file or inline text) that is not valid YAML/JSON.
    #[error("openapi source {label}: {message}")]
    OpenApiSpecParse { label: String, message: String },
}
