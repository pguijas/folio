//! The retained cache across batches: a
//! keyed store of parsed payloads with the hash of the source they came
//! from. The handler works on a clone and assigns it back only after the
//! manifest is saved, so a failed batch never caches new bytes with old IR;
//! the loop keeps the pending edits (`Batch::merge`).

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

/// One retained result: the SHA-256 of the source bytes it was parsed from
/// and the parsed payload (a `ModuleIR` in the binary).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Entry<T> {
    pub hash: String,
    pub payload: T,
}

/// Parsed results keyed by source path, in path order.
#[derive(Debug, Clone)]
pub struct RetainedCache<T> {
    entries: BTreeMap<PathBuf, Entry<T>>,
}

// A derive would demand `T: Default`; an empty cache needs no payload.
impl<T> Default for RetainedCache<T> {
    fn default() -> Self {
        RetainedCache {
            entries: BTreeMap::new(),
        }
    }
}

impl<T> RetainedCache<T> {
    /// Replace the entry for `path` or add it.
    pub fn upsert(&mut self, path: PathBuf, hash: impl Into<String>, payload: T) {
        self.entries.insert(
            path,
            Entry {
                hash: hash.into(),
                payload,
            },
        );
    }

    /// Drop the entry for `path` (a deleted, excluded or renamed source).
    pub fn remove(&mut self, path: &Path) {
        self.entries.remove(path);
    }

    /// The entry for `path`.
    pub fn get(&self, path: &Path) -> Option<&Entry<T>> {
        self.entries.get(path)
    }

    /// Number of retained entries.
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// No retained entries.
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Retained source paths in path order.
    pub fn paths(&self) -> impl Iterator<Item = &Path> {
        self.entries.keys().map(PathBuf::as_path)
    }

    /// Retained payloads in path order.
    pub fn payloads(&self) -> impl Iterator<Item = &T> {
        self.entries.values().map(|e| &e.payload)
    }

    /// Paths whose current hash (`hash_of(path)`, `""` when the file is gone)
    /// differs from the retained one: edited before the watcher started or
    /// part of a failed batch.
    pub fn stale(&self, hash_of: impl Fn(&Path) -> String) -> Vec<PathBuf> {
        self.entries
            .iter()
            .filter(|(path, entry)| hash_of(path) != entry.hash)
            .map(|(path, _)| path.clone())
            .collect()
    }
}

#[cfg(test)]
#[path = "cache_tests.rs"]
mod tests;
