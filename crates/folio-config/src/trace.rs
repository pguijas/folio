//! The `FOLIO_TRACE` JSONL writer: one JSON line per
//! event with `event`, `t_ns`, `wall_ms`, `batch` and the caller's fields.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::Instant;

use serde_json::{json, Value};

/// The file path that switches tracing on.
pub const TRACE_ENV_VAR: &str = "FOLIO_TRACE";

/// An open trace file. Shared across threads through `&self`; the writes are
/// serialised so the watcher and its callbacks can both emit.
#[derive(Debug)]
pub struct Tracer {
    path: PathBuf,
    start: Instant,
    inner: Mutex<Inner>,
}

#[derive(Debug)]
struct Inner {
    file: File,
    batch: u64,
}

impl Tracer {
    /// `FOLIO_TRACE` trimmed and non-empty opens that file; `Err` is the
    /// warning to show (`FOLIO_TRACE: cannot open {path}: {error}; tracing disabled`).
    pub fn from_env() -> Result<Option<Tracer>, String> {
        let raw = std::env::var(TRACE_ENV_VAR).unwrap_or_default();
        let raw = raw.trim();
        if raw.is_empty() {
            return Ok(None);
        }
        Tracer::open(Path::new(raw)).map(Some)
    }

    /// Open `path` for appending, creating parent directories.
    pub fn open(path: &Path) -> Result<Tracer, String> {
        let open = || {
            if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
                std::fs::create_dir_all(parent)?;
            }
            OpenOptions::new().append(true).create(true).open(path)
        };
        let file = open().map_err(|e| {
            format!(
                "FOLIO_TRACE: cannot open {}: {e}; tracing disabled",
                path.display()
            )
        })?;
        Ok(Tracer {
            path: path.to_path_buf(),
            start: Instant::now(),
            inner: Mutex::new(Inner { file, batch: 0 }),
        })
    }

    /// The file being written.
    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Append one event; `batch_start` advances the batch counter first.
    pub fn trace(&self, event: &str, fields: &[(&str, Value)]) {
        let mut inner = self
            .inner
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        if event == "batch_start" {
            inner.batch += 1;
        }
        let mut record = serde_json::Map::new();
        record.insert("event".into(), json!(event));
        record.insert("t_ns".into(), json!(self.start.elapsed().as_nanos() as u64));
        record.insert(
            "wall_ms".into(),
            json!(jiff::Timestamp::now().as_microsecond() as f64 / 1000.0),
        );
        record.insert("batch".into(), json!(inner.batch));
        for (key, value) in fields {
            record.insert((*key).into(), value.clone());
        }
        // ponytail: a failed write is dropped; tracing is diagnostics, never the build.
        let _ = writeln!(inner.file, "{}", Value::Object(record));
        let _ = inner.file.flush();
    }
}
