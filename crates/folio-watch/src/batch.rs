//! The batch loop: one debounced set of
//! raw events becomes one classified `Batch` handed to the `BatchHandler`
//! the binary implements; a failed batch keeps its edits for the next save
//! and the loop never dies on a handler error.

use std::collections::BTreeSet;
use std::fmt;
use std::path::{Path, PathBuf};
use std::sync::mpsc::Receiver;

use folio_config::trace::Tracer;
use serde_json::json;

use crate::events::{coalesce, collect_set, ChangeKind, Debounce, RawEvent};
use crate::filter::{Batch, WatchConfig};

/// What a refreshed batch produced (`batch_end` fields plus warnings).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct BatchSummary {
    pub pages: usize,
    pub skipped: usize,
    pub warnings: Vec<String>,
}

/// One source batch. Any `Err` aborts the set and its edits stay pending for
/// the next save.
pub trait BatchHandler {
    /// Changes under the directories built-ins asked to watch, with the
    /// final kind; `Ok(true)` when one handled it (a republish follows).
    fn plugin_dirs_changed(&mut self, changes: &[(PathBuf, ChangeKind)]) -> Result<bool, String>;
    /// The source-change paths of one save (sources, guides, assets): stage,
    /// generate, refresh contract/search/LLM outputs, save the manifest,
    /// commit the retained cache. `refresh_extensions` when a plugin handled
    /// a change in this batch.
    fn refresh(
        &mut self,
        paths: &BTreeSet<PathBuf>,
        refresh_extensions: bool,
    ) -> Result<BatchSummary, String>;
    /// A file under `docs/examples` changed: rebuild the preview examples.
    fn refresh_previews(&mut self, path: &Path) -> Result<(), String>;
}

/// What the loop reports; the binary prints it (`Display` is the text).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Event {
    /// A handler warning, verbatim.
    Warning(String),
    /// A batch committed (`verbose` line).
    BatchDone { pages: usize, skipped: usize },
    /// Preview examples rebuilt; the path relative to `project_dir/docs`.
    PreviewsRefreshed(String),
    /// The set failed; its edits are retried on the next save.
    Error(String),
}

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Event::Warning(text) => f.write_str(text),
            Event::BatchDone { pages, skipped } => {
                write!(f, "Source batch: {pages} pages, {skipped} reused")
            }
            Event::PreviewsRefreshed(path) => write!(f, "Updated preview examples: {path}"),
            Event::Error(message) => write!(
                f,
                "Watcher error: {message}. Batch not committed; retry on next save."
            ),
        }
    }
}

/// Run until the channel closes (the `notify` watcher or the test sender is
/// dropped). Each debounced set is coalesced, classified, merged with the
/// edits of a failed earlier set, and handed to `handler`.
pub fn run_loop(
    rx: &Receiver<RawEvent>,
    cfg: &WatchConfig,
    debounce: Debounce,
    handler: &mut dyn BatchHandler,
    tracer: Option<&Tracer>,
    on_event: &mut dyn FnMut(Event),
) {
    let mut pending = Batch::default();
    let mut refresh_extensions = false;
    while let Some(set) = collect_set(rx, debounce) {
        let set: Vec<RawEvent> = set
            .into_iter()
            .filter(|event| cfg.subscribed(&event.path))
            .collect();
        if set.is_empty() {
            continue;
        }
        trace(tracer, "watcher_event", &[("n_raw", json!(set.len()))]);
        pending.merge(cfg.batch(&coalesce(&set)));
        if pending.is_empty() {
            continue;
        }
        let result = run_set(
            &mut pending,
            &mut refresh_extensions,
            cfg,
            handler,
            tracer,
            on_event,
        );
        if let Err(message) = result {
            on_event(Event::Error(message));
        }
    }
}

/// One set: plugin dispatch, the source batch, then the previews. Every
/// piece clears its own part of `pending` only after it succeeded.
fn run_set(
    pending: &mut Batch,
    refresh_extensions: &mut bool,
    cfg: &WatchConfig,
    handler: &mut dyn BatchHandler,
    tracer: Option<&Tracer>,
    on_event: &mut dyn FnMut(Event),
) -> Result<(), String> {
    if !pending.plugin_changes.is_empty() {
        let changes: Vec<(PathBuf, ChangeKind)> = pending
            .plugin_changes
            .iter()
            .map(|(path, kind)| (path.clone(), *kind))
            .collect();
        *refresh_extensions |= handler.plugin_dirs_changed(&changes)?;
        pending.plugin_changes.clear();
    }
    if !pending.paths.is_empty() || *refresh_extensions {
        trace(
            tracer,
            "batch_start",
            &[("n_paths", json!(pending.paths.len()))],
        );
        let summary = handler.refresh(&pending.paths, *refresh_extensions)?;
        trace(tracer, "manifest_saved", &[]);
        trace(
            tracer,
            "batch_end",
            &[
                ("pages", json!(summary.pages)),
                ("skipped", json!(summary.skipped)),
            ],
        );
        pending.paths.clear();
        *refresh_extensions = false;
        for warning in summary.warnings {
            on_event(Event::Warning(warning));
        }
        on_event(Event::BatchDone {
            pages: summary.pages,
            skipped: summary.skipped,
        });
    }
    if let Some(path) = pending.preview_changed.clone() {
        handler.refresh_previews(&path)?;
        pending.preview_changed = None;
        let shown = cfg
            .preview_examples
            .as_deref()
            .and_then(Path::parent)
            .and_then(|docs| path.strip_prefix(docs).ok())
            .unwrap_or(&path);
        on_event(Event::PreviewsRefreshed(
            shown.to_string_lossy().replace('\\', "/"),
        ));
    }
    Ok(())
}

fn trace(tracer: Option<&Tracer>, event: &str, fields: &[(&str, serde_json::Value)]) {
    if let Some(t) = tracer {
        t.trace(event, fields);
    }
}
