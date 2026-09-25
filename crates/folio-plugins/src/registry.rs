//! `ExtensionRegistry`: components, layouts, data modules and views a build
//! composes into the template workspace.

use std::path::PathBuf;

use indexmap::IndexMap;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::error::PluginsError;
use crate::Diagnostics;

/// Where a component came from; a builtin may be shadowed, anything else may not.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ComponentOrigin {
    Builtin,
    Config,
    Plugin,
}

impl std::fmt::Display for ComponentOrigin {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            ComponentOrigin::Builtin => "builtin",
            ComponentOrigin::Config => "config",
            ComponentOrigin::Plugin => "plugin",
        })
    }
}

/// One MDX/TSX component the workspace can import.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComponentDefinition {
    /// JS identifier the component is exposed as.
    pub name: String,
    /// `@/components/...` import path.
    pub import_path: String,
    /// `None` = named export `name`; `Some("default")` = default export.
    pub export_name: Option<String>,
    /// Injected into `mdx-components.tsx`.
    pub expose_mdx: bool,
    /// A source file the emitter copies into the workspace.
    pub source_path: Option<PathBuf>,
    /// Prop name to TS type text, declaration order kept.
    pub props: IndexMap<String, String>,
    /// A custom template must wire it.
    pub required: bool,
    /// Taxonomy only.
    pub category: String,
    /// Published MDX contract membership (explicit, never inferred).
    pub contract: bool,
    /// The contract `source` string.
    pub source_label: String,
    pub origin: ComponentOrigin,
}

impl ComponentDefinition {
    /// The defaults: `expose_mdx`, category `general`, origin `plugin`.
    pub fn new(name: &str, import_path: &str) -> Self {
        ComponentDefinition {
            name: name.to_string(),
            import_path: import_path.to_string(),
            export_name: None,
            expose_mdx: true,
            source_path: None,
            props: IndexMap::new(),
            required: false,
            category: "general".to_string(),
            contract: false,
            source_label: String::new(),
            origin: ComponentOrigin::Plugin,
        }
    }

    /// The name the import statement binds: `export_name` or `name`.
    pub fn imported_name(&self) -> &str {
        self.export_name.as_deref().unwrap_or(&self.name)
    }
}

/// A page layout a view renders inside.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LayoutDefinition {
    pub name: String,
    pub import_path: String,
    pub export_name: String,
    pub slots: Vec<String>,
}

/// A typed `lib/<module_path>.ts` data module.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct DataModuleDefinition {
    pub name: String,
    pub export_name: String,
    pub data: Value,
    pub type_source: String,
    pub type_annotation: String,
    /// Path under `lib/` without `.ts`; `""` = `__folio_data/<name>`.
    pub module_path: String,
}

/// One component instance inside a view slot.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ViewBlock {
    pub component: String,
    pub props: serde_json::Map<String, Value>,
}

/// A generated `app/<path>/page.tsx`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ViewDefinition {
    /// Normalized `/x/y` or `/`.
    pub path: String,
    pub layout: String,
    pub slots: IndexMap<String, Vec<ViewBlock>>,
    pub title: String,
    pub props: serde_json::Map<String, Value>,
}

/// `^[A-Za-z_$][A-Za-z0-9_$]*$`.
pub fn is_js_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    match chars.next() {
        Some(c) if c.is_ascii_alphabetic() || c == '_' || c == '$' => {}
        _ => return false,
    }
    chars.all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '$')
}

fn identifier(value: &str, label: &'static str) -> Result<(), PluginsError> {
    if is_js_identifier(value) {
        Ok(())
    } else {
        Err(PluginsError::InvalidIdentifier {
            label,
            value: value.to_string(),
        })
    }
}

/// Everything the build composes into the workspace, in registration order.
#[derive(Debug, Default)]
pub struct ExtensionRegistry {
    pub components: IndexMap<String, ComponentDefinition>,
    pub layouts: IndexMap<String, LayoutDefinition>,
    pub data_modules: IndexMap<String, DataModuleDefinition>,
    pub views: IndexMap<String, ViewDefinition>,
}

impl ExtensionRegistry {
    /// Shadowing a builtin from another origin warns and replaces it in place;
    /// any other repeat fails.
    pub fn register_component(
        &mut self,
        def: ComponentDefinition,
        diag: &mut Diagnostics,
    ) -> Result<&ComponentDefinition, PluginsError> {
        identifier(&def.name, "component name")?;
        if let Some(export) = &def.export_name {
            identifier(export, "component export")?;
        }
        if let Some(existing) = self.components.get(&def.name) {
            if existing.origin == ComponentOrigin::Builtin && def.origin != ComponentOrigin::Builtin
            {
                diag.push(format!(
                    "Component '{}' overrides the Folio builtin of the same name",
                    def.name
                ));
            } else {
                return Err(PluginsError::ComponentRegistered {
                    name: def.name.clone(),
                    existing: existing.origin,
                    new: def.origin,
                });
            }
        }
        let name = def.name.clone();
        self.components.insert(name.clone(), def);
        Ok(&self.components[&name])
    }

    /// A layout views render inside: the name must be new, the export and
    /// every slot identifiers, and there must be at least one slot.
    pub fn register_layout(
        &mut self,
        name: &str,
        import_path: &str,
        export_name: &str,
        slots: &[&str],
    ) -> Result<&LayoutDefinition, PluginsError> {
        if self.layouts.contains_key(name) {
            return Err(PluginsError::LayoutRegistered(name.to_string()));
        }
        identifier(export_name, "layout export")?;
        if slots.is_empty() {
            return Err(PluginsError::LayoutWithoutSlots);
        }
        for slot in slots {
            identifier(slot, "layout slot")?;
        }
        let layout = LayoutDefinition {
            name: name.to_string(),
            import_path: import_path.to_string(),
            export_name: export_name.to_string(),
            slots: slots.iter().map(|s| s.to_string()).collect(),
        };
        self.layouts.insert(name.to_string(), layout);
        Ok(&self.layouts[name])
    }

    /// A typed data module: the export must be an identifier, the name new.
    pub fn write_data_module(
        &mut self,
        def: DataModuleDefinition,
    ) -> Result<&DataModuleDefinition, PluginsError> {
        identifier(&def.export_name, "data export")?;
        if self.data_modules.contains_key(&def.name) {
            return Err(PluginsError::DataModuleRegistered(def.name));
        }
        let name = def.name.clone();
        self.data_modules.insert(name.clone(), def);
        Ok(&self.data_modules[&name])
    }

    /// `path` is normalized to `"/" + path.trim_matches('/')`.
    pub fn add_view(
        &mut self,
        path: &str,
        layout: &str,
        slots: IndexMap<String, Vec<ViewBlock>>,
        title: &str,
        props: serde_json::Map<String, Value>,
    ) -> Result<&ViewDefinition, PluginsError> {
        let path = format!("/{}", path.trim_matches('/'));
        if self.views.contains_key(&path) {
            return Err(PluginsError::ViewRegistered(path));
        }
        let Some(layout_def) = self.layouts.get(layout) else {
            return Err(PluginsError::UnknownLayout {
                path,
                layout: layout.to_string(),
            });
        };
        for (slot, blocks) in &slots {
            if !layout_def.slots.contains(slot) {
                return Err(PluginsError::UnknownSlot {
                    layout: layout.to_string(),
                    slot: slot.clone(),
                });
            }
            for block in blocks {
                if !self.components.contains_key(&block.component) {
                    return Err(PluginsError::UnknownComponent {
                        path,
                        component: block.component.clone(),
                    });
                }
            }
        }
        let view = ViewDefinition {
            path: path.clone(),
            layout: layout.to_string(),
            slots,
            title: title.to_string(),
            props,
        };
        self.views.insert(path.clone(), view);
        Ok(&self.views[&path])
    }

    /// The components flagged `contract`, in registry order.
    pub fn contract_components(&self) -> impl Iterator<Item = &ComponentDefinition> {
        self.components.values().filter(|c| c.contract)
    }
}

#[cfg(test)]
#[path = "registry_tests.rs"]
mod tests;
