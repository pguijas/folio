//! Nextra `_meta.ts` generation: root ordering, per-directory files, the
//! `Source Code` tree grouped by language, hidden and unlisted entries.

use std::collections::{BTreeMap, BTreeSet};

use folio_config::{language_label, slug_label, slugify};
use indexmap::IndexMap;

use crate::re;

/// One published Markdown page as the sidebar sees it.
pub struct SidebarPage<'a> {
    /// Content route without docs base or extension (`components/callout`).
    pub route: &'a str,
    /// Frontmatter title (already "frontmatter, else first H1").
    pub title: Option<&'a str>,
    /// Hidden from the sidebar, published everywhere else.
    pub unlisted: bool,
}

/// One parsed source module as the sidebar sees it.
pub struct SidebarModule<'a> {
    /// Route below `api-reference/`, e.g. `mylib/core` or `rust/geo/shapes`.
    pub route_below_api: &'a str,
    /// The parser's language id (`python`, `rust`, ...).
    pub language: &'a str,
}

/// Everything `generate_meta_files` needs.
pub struct SidebarInput<'a> {
    /// `docs.yaml` `nav`.
    pub nav: &'a [String],
    /// Every published module, Python first.
    pub modules: &'a [SidebarModule<'a>],
    /// Every published Markdown page in discovery order.
    pub pages: &'a [SidebarPage<'a>],
    /// `sidebar.default_collapsed`; folders start collapsed when true.
    pub default_collapsed: bool,
}

/// A `_meta.ts` value.
#[derive(Debug, Clone, PartialEq)]
pub enum MetaValue {
    /// A page title or expanded folder title.
    Str(String),
    /// `true`/`false` (the `collapsed` flag).
    Bool(bool),
    /// A nested object (hidden entry, collapsed folder, separator).
    Object(Meta),
}

/// An ordered `_meta.ts` object.
pub type Meta = IndexMap<String, MetaValue>;

const SOURCE_CODE_SLUG: &str = "api-reference";
const SOURCE_CODE_TITLE: &str = "Source Code";

/// A compiled-in page order entry.
pub enum OrderEntry {
    /// `(slug, title)` of a page.
    Page(&'static str, &'static str),
    /// `(slug, title, children)` of a directory with its own order.
    Dir(&'static str, &'static str, &'static [OrderEntry]),
}

use OrderEntry::{Dir, Page};

/// Folio's own docs order; it applies to every project.
/// The reader's path first (install, first build, configure, write), then
/// the site's parts, then migration and help, then the contributor pages.
/// Components follow the groups of the components overview; plugins list
/// the ones this release ships before the ones it does not.
pub static DOC_PAGE_ORDER: &[OrderEntry] = &[
    Page("index", "Overview"),
    Page("introduction", "Introduction"),
    Page("why-folio", "Why Folio"),
    Page("installation", "Installation"),
    Page("quickstart", "Quick Start"),
    Page("configuration", "Configuration"),
    Page("cli", "CLI Reference"),
    Page("languages", "Languages"),
    Page("docstrings", "Writing Doc Comments"),
    Dir(
        "components",
        "Components",
        &[
            Page("index", "Overview"),
            Page("terminal-session", "TerminalSession"),
            Page("config-panel", "ConfigPanel"),
            Page("build-artifact", "BuildArtifact"),
            Page("command-grid", "CommandGrid"),
            Page("before-after", "BeforeAfter"),
            Page("checklist", "Checklist"),
            Page("hook-map", "HookMap"),
            Page("accordion", "Accordion"),
            Page("tabs", "Tabs"),
            Page("steps", "Steps"),
            Page("timeline", "Timeline"),
            Page("code-group", "CodeGroup"),
            Page("preview-code", "PreviewCode"),
            Page("example-tabs", "ExampleTabs"),
            Page("callout", "Callout"),
            Page("feature-cards", "FeatureCard & CardGrid"),
            Page("file-tree", "FileTree"),
            Page("doc-preview", "DocPreview"),
            Page("browser-frame", "BrowserFrame"),
            Page("mermaid", "Mermaid"),
            Page("math", "Math (LaTeX)"),
            Page("code-blocks", "Code Blocks"),
            Page("stat-strip", "StatStrip"),
            Page("pull-quote", "PullQuote"),
            Page("compare-matrix", "CompareMatrix"),
            Page("swot", "Swot"),
            Page("class-overview", "ClassOverview"),
            Page("method-accordion", "MethodAccordion"),
            Page("param-table", "ParamTable"),
            Page("type-badge", "TypeBadge"),
            Page("deprecation-notice", "DeprecationNotice"),
            Page("theme-configurator", "ThemeConfigurator"),
            Page("copy-page-button", "Page Actions"),
        ],
    ),
    Dir(
        "theming",
        "Theming",
        &[
            Page("index", "Overview"),
            Page("personalization", "Personalization"),
            Page("theme-packages", "Theme Packages"),
            Page("custom-templates", "Custom Templates"),
        ],
    ),
    Dir(
        "deployment",
        "Deployment",
        &[
            Page("index", "Overview"),
            Page("static-hosts", "Static Hosts"),
            Page("github-pages", "GitHub Pages"),
            Page("ci-cd", "CI/CD"),
        ],
    ),
    Dir(
        "plugins",
        "Plugins",
        &[
            Page("index", "Overview"),
            Page("roadmap", "Roadmap"),
            Page("openapi", "OpenAPI"),
            Page("landing", "Landing Page"),
            Page("catalog", "Catalog"),
            Page("authoring", "Writing Plugins"),
            Page("trust", "Trust & Safety"),
        ],
    ),
    Page("migration", "Migration Guide"),
    Page("troubleshooting", "Troubleshooting"),
    Page("architecture", "Architecture"),
    Page("developing", "Developer Guide"),
];

impl OrderEntry {
    fn slug(&self) -> &'static str {
        match self {
            Page(slug, _) | Dir(slug, _, _) => slug,
        }
    }
    fn title(&self) -> &'static str {
        match self {
            Page(_, title) | Dir(_, title, _) => title,
        }
    }
}

/// The declared `(slug, title)` order of a docs directory; empty when nothing
/// declares that path.
pub fn declared_order(path: &[&str]) -> Vec<(&'static str, &'static str)> {
    let mut entries = DOC_PAGE_ORDER;
    for segment in path {
        match entries
            .iter()
            .find(|e| e.slug() == *segment && matches!(e, Dir(..)))
        {
            Some(Dir(_, _, children)) => entries = children,
            _ => return Vec::new(),
        }
    }
    entries.iter().map(|e| (e.slug(), e.title())).collect()
}

/// The emoji class stripped from sidebar labels.
pub fn emoji_pattern() -> regex::Regex {
    re("[\u{200d}\u{2300}-\u{23ff}\u{2600}-\u{27bf}\u{fe0e}\u{fe0f}\u{1f000}-\u{1faff}]+")
}

/// Emoji-free, whitespace-collapsed sidebar label with a fallback.
pub fn sidebar_title(title: Option<&str>, fallback: &str) -> String {
    sidebar_title_with(title, fallback, &emoji_pattern())
}

/// `sidebar_title` with the emoji pattern compiled by the caller.
pub fn sidebar_title_with(title: Option<&str>, fallback: &str, emoji: &regex::Regex) -> String {
    let raw = match title {
        Some(t) if !t.trim().is_empty() => t,
        _ => fallback,
    };
    let cleaned = emoji.replace_all(raw, "");
    let cleaned = cleaned.split_whitespace().collect::<Vec<_>>().join(" ");
    if cleaned.is_empty() {
        fallback.to_string()
    } else {
        cleaned
    }
}

fn escape(text: &str) -> String {
    text.replace('\\', "\\\\").replace('"', "\\\"")
}

fn value_lines(value: &MetaValue, indent: usize) -> Vec<String> {
    match value {
        MetaValue::Object(entries) => {
            let mut lines = vec!["{".to_string()];
            let pad = " ".repeat(indent + 2);
            for (key, child) in entries {
                let rendered = value_lines(child, indent + 2);
                if rendered.len() == 1 {
                    lines.push(format!("{pad}\"{}\": {},", escape(key), rendered[0]));
                } else {
                    lines.push(format!("{pad}\"{}\": {}", escape(key), rendered[0]));
                    lines.extend(rendered[1..rendered.len() - 1].iter().cloned());
                    lines.push(format!("{pad}{},", rendered[rendered.len() - 1]));
                }
            }
            lines.push("}".to_string());
            lines
        }
        MetaValue::Bool(b) => vec![b.to_string()],
        MetaValue::Str(s) => vec![format!("\"{}\"", escape(s))],
    }
}

/// `export default { ... }` serialiser; no trailing newline.
pub fn meta_to_ts(meta: &Meta) -> String {
    let mut lines = value_lines(&MetaValue::Object(meta.clone()), 0);
    lines[0] = "export default {".to_string();
    lines.join("\n")
}

fn hidden() -> MetaValue {
    MetaValue::Object(IndexMap::from([(
        "display".to_string(),
        MetaValue::Str("hidden".to_string()),
    )]))
}

fn folder_meta(title: &str, default_collapsed: bool) -> MetaValue {
    if !default_collapsed {
        return MetaValue::Str(title.to_string());
    }
    MetaValue::Object(IndexMap::from([
        ("title".to_string(), MetaValue::Str(title.to_string())),
        (
            "theme".to_string(),
            MetaValue::Object(IndexMap::from([(
                "collapsed".to_string(),
                MetaValue::Bool(true),
            )])),
        ),
    ]))
}

type DirPath = Vec<String>;

struct DocMeta {
    pages_by_dir: BTreeMap<DirPath, IndexMap<String, String>>,
    dirs_by_dir: BTreeMap<DirPath, IndexMap<String, String>>,
    unlisted: BTreeSet<Vec<String>>,
    default_collapsed: bool,
}

impl DocMeta {
    fn collect(pages: &[SidebarPage], default_collapsed: bool) -> Self {
        let mut this = DocMeta {
            pages_by_dir: BTreeMap::new(),
            dirs_by_dir: BTreeMap::new(),
            unlisted: BTreeSet::new(),
            default_collapsed,
        };
        let emoji = emoji_pattern();
        for page in pages {
            let parts: Vec<String> = page
                .route
                .split('/')
                .filter(|p| !p.is_empty())
                .map(str::to_string)
                .collect();
            let Some((slug, dir_path)) = parts.split_last() else {
                continue;
            };
            let title = sidebar_title_with(page.title, &slug_label(slug), &emoji);
            this.pages_by_dir
                .entry(dir_path.to_vec())
                .or_default()
                .insert(slug.clone(), title);
            if page.unlisted {
                this.unlisted.insert(parts.clone());
            }
            for (index, dir_slug) in dir_path.iter().enumerate() {
                this.dirs_by_dir
                    .entry(dir_path[..index].to_vec())
                    .or_default()
                    .entry(dir_slug.clone())
                    .or_insert_with(|| slug_label(dir_slug));
            }
        }
        let pages_by_dir = &this.pages_by_dir;
        for (parent, children) in this.dirs_by_dir.iter_mut() {
            for (child_slug, title) in children.iter_mut() {
                let mut child_path = parent.clone();
                child_path.push(child_slug.clone());
                if let Some(index_title) =
                    pages_by_dir.get(&child_path).and_then(|p| p.get("index"))
                {
                    *title = index_title.clone();
                }
            }
        }
        this
    }

    fn subtree_unlisted(&self, dir: &[String]) -> bool {
        self.pages_by_dir.iter().all(|(page_dir, pages)| {
            !page_dir.starts_with(dir)
                || pages.keys().all(|slug| {
                    let mut full = page_dir.clone();
                    full.push(slug.clone());
                    self.unlisted.contains(&full)
                })
        })
    }

    fn entry_value(&self, path: &[String], slug: &str, title: &str) -> MetaValue {
        let mut full = path.to_vec();
        full.push(slug.to_string());
        if self
            .dirs_by_dir
            .get(path)
            .map(|d| d.contains_key(slug))
            .unwrap_or(false)
        {
            if self.subtree_unlisted(&full) {
                return hidden();
            }
            return folder_meta(title, self.default_collapsed);
        }
        if self.unlisted.contains(&full) {
            return hidden();
        }
        MetaValue::Str(title.to_string())
    }

    fn build_meta_for_dir(&self, path: &[String]) -> Meta {
        let mut remaining: IndexMap<String, String> = IndexMap::new();
        if let Some(pages) = self.pages_by_dir.get(path) {
            remaining.extend(pages.iter().map(|(k, v)| (k.clone(), v.clone())));
        }
        if let Some(dirs) = self.dirs_by_dir.get(path) {
            for (k, v) in dirs {
                remaining.insert(k.clone(), v.clone());
            }
        }
        let mut ordered = Meta::new();
        if !path.is_empty() && remaining.shift_remove("index").is_some() {
            ordered.insert("index".to_string(), hidden());
        }
        let segments: Vec<&str> = path.iter().map(String::as_str).collect();
        for (slug, _) in declared_order(&segments) {
            if let Some(title) = remaining.shift_remove(slug) {
                ordered.insert(slug.to_string(), self.entry_value(path, slug, &title));
            }
        }
        for (slug, title) in &remaining {
            ordered.insert(slug.clone(), self.entry_value(path, slug, title));
        }
        ordered
    }

    fn all_dirs(&self) -> BTreeSet<DirPath> {
        self.pages_by_dir
            .keys()
            .chain(self.dirs_by_dir.keys())
            .cloned()
            .collect()
    }
}

fn move_to_end(meta: &mut Meta, slug: &str) {
    if let Some(value) = meta.shift_remove(slug) {
        meta.insert(slug.to_string(), value);
    }
}

fn apply_nav_order(meta: Meta, nav: &[String]) -> Meta {
    if nav.is_empty() {
        return meta;
    }
    let mut aliases: BTreeMap<String, String> = BTreeMap::new();
    for (key, value) in &meta {
        aliases.insert(slugify(key), key.clone());
        let title = match value {
            MetaValue::Str(s) => Some(s),
            MetaValue::Object(o) => match o.get("title") {
                Some(MetaValue::Str(s)) => Some(s),
                _ => None,
            },
            MetaValue::Bool(_) => None,
        };
        if let Some(title) = title {
            aliases.insert(slugify(title), key.clone());
        }
    }
    let mut ordered = Meta::new();
    for item in nav {
        let mut slug = slugify(item);
        if slug == "guide" {
            for (key, value) in &meta {
                if key != SOURCE_CODE_SLUG {
                    ordered.entry(key.clone()).or_insert_with(|| value.clone());
                }
            }
            continue;
        }
        if slug == "source-code" {
            slug = SOURCE_CODE_SLUG.to_string();
        }
        if let Some(key) = aliases.get(&slug) {
            ordered
                .entry(key.clone())
                .or_insert_with(|| meta[key].clone());
        }
    }
    for (key, value) in meta {
        ordered.entry(key).or_insert(value);
    }
    ordered
}

enum Tree {
    Leaf,
    Node(IndexMap<String, Tree>),
}

fn build_module_tree(modules: &[SidebarModule]) -> IndexMap<String, Tree> {
    let mut tree = IndexMap::new();
    let mut sorted: Vec<&SidebarModule> = modules.iter().collect();
    sorted.sort_by_key(|m| m.language != "python");
    for module in sorted {
        let parts: Vec<&str> = module.route_below_api.split('/').collect();
        let mut node = &mut tree;
        for part in &parts[..parts.len() - 1] {
            let entry = node
                .entry(part.to_string())
                .or_insert_with(|| Tree::Node(IndexMap::new()));
            if matches!(entry, Tree::Leaf) {
                *entry = Tree::Node(IndexMap::new());
            }
            node = match entry {
                Tree::Node(children) => children,
                Tree::Leaf => unreachable!(),
            };
        }
        node.entry(parts[parts.len() - 1].to_string())
            .or_insert(Tree::Leaf);
    }
    tree
}

fn language_groups(modules: &[SidebarModule]) -> (Meta, BTreeMap<String, String>) {
    let mut languages: Vec<&str> = Vec::new();
    let mut sorted: Vec<&SidebarModule> = modules.iter().collect();
    sorted.sort_by_key(|m| m.language != "python");
    for module in sorted {
        if !languages.contains(&module.language) {
            languages.push(module.language);
        }
    }
    let titles = languages
        .iter()
        .filter(|l| **l != "python")
        .map(|l| (l.to_string(), language_label(l)))
        .collect();
    let mut leading = Meta::new();
    if languages.len() > 1 && languages.contains(&"python") {
        leading.insert(
            "---python".to_string(),
            MetaValue::Object(IndexMap::from([
                ("type".to_string(), MetaValue::Str("separator".to_string())),
                (
                    "title".to_string(),
                    MetaValue::Str(language_label("python")),
                ),
            ])),
        );
    }
    (leading, titles)
}

fn generate_meta_from_tree(
    tree: &IndexMap<String, Tree>,
    prefix: &str,
    result: &mut BTreeMap<String, String>,
    include_index: bool,
    default_collapsed: bool,
    leading: &Meta,
    titles: &BTreeMap<String, String>,
) {
    let mut meta = Meta::new();
    if include_index {
        meta.insert("index".to_string(), hidden());
    }
    for (key, value) in leading {
        meta.insert(key.clone(), value.clone());
    }
    for (key, subtree) in tree {
        match subtree {
            Tree::Node(children) if !children.is_empty() => {
                let title = titles.get(key).cloned().unwrap_or_else(|| slug_label(key));
                meta.insert(key.clone(), folder_meta(&title, default_collapsed));
                generate_meta_from_tree(
                    children,
                    &format!("{prefix}/{key}"),
                    result,
                    false,
                    default_collapsed,
                    &Meta::new(),
                    titles,
                );
            }
            _ => {
                meta.insert(key.clone(), MetaValue::Str(slug_label(key)));
            }
        }
    }
    result.insert(format!("{prefix}/_meta.ts"), meta_to_ts(&meta));
}

/// Every `_meta.ts` the content tree needs: content-relative path to file text.
pub fn generate_meta_files(input: &SidebarInput) -> BTreeMap<String, String> {
    let mut result = BTreeMap::new();
    let mut root = Meta::new();
    if !input.pages.is_empty() {
        let docs = DocMeta::collect(input.pages, input.default_collapsed);
        root = docs.build_meta_for_dir(&[]);
        for dir in docs.all_dirs().into_iter().filter(|d| !d.is_empty()) {
            result.insert(
                format!("{}/_meta.ts", dir.join("/")),
                meta_to_ts(&docs.build_meta_for_dir(&dir)),
            );
        }
    }
    if !input.modules.is_empty() {
        root.insert(
            SOURCE_CODE_SLUG.to_string(),
            folder_meta(SOURCE_CODE_TITLE, input.default_collapsed),
        );
    }
    move_to_end(&mut root, "contributing");
    move_to_end(&mut root, SOURCE_CODE_SLUG);
    let root = apply_nav_order(root, input.nav);
    result.insert("_meta.ts".to_string(), meta_to_ts(&root));
    if !input.modules.is_empty() {
        let tree = build_module_tree(input.modules);
        let (leading, titles) = language_groups(input.modules);
        generate_meta_from_tree(
            &tree,
            SOURCE_CODE_SLUG,
            &mut result,
            true,
            input.default_collapsed,
            &leading,
            &titles,
        );
    }
    result
}

#[cfg(test)]
#[path = "sidebar_tests.rs"]
mod tests;
