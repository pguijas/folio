//! Raw filesystem events: the `notify` source, the in-memory channel the
//! tests feed, the debounced set collector and per-path coalescing.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender};
use std::time::{Duration, Instant};

use notify::event::{ModifyKind, RenameMode};
use notify::{EventKind, RecursiveMode, Watcher};

use crate::WatchError;

/// The `watchfiles.Change` names: `added`, `modified`, `deleted`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChangeKind {
    Added,
    Modified,
    Deleted,
}

impl ChangeKind {
    /// The lowercase name plugin dispatch receives.
    pub fn name(self) -> &'static str {
        match self {
            ChangeKind::Added => "added",
            ChangeKind::Modified => "modified",
            ChangeKind::Deleted => "deleted",
        }
    }
}

/// One raw event as the OS layer (or a test) delivers it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RawEvent {
    pub kind: ChangeKind,
    pub path: PathBuf,
}

/// The two debounce constants (the `watchfiles` library's defaults):
/// a set closes after `quiet` without events, or `cap` after its first one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Debounce {
    pub quiet: Duration,
    pub cap: Duration,
}

impl Default for Debounce {
    fn default() -> Self {
        Debounce {
            quiet: Duration::from_millis(50),
            cap: Duration::from_millis(1600),
        }
    }
}

/// Block for the next debounced set of raw events; `None` once every sender
/// is gone (the watcher was dropped), which ends the loop.
pub fn collect_set(rx: &Receiver<RawEvent>, debounce: Debounce) -> Option<Vec<RawEvent>> {
    let mut set = vec![rx.recv().ok()?];
    let started = Instant::now();
    loop {
        let Some(remaining) = debounce.cap.checked_sub(started.elapsed()) else {
            return Some(set);
        };
        match rx.recv_timeout(remaining.min(debounce.quiet)) {
            Ok(event) => set.push(event),
            Err(RecvTimeoutError::Timeout) => return Some(set),
            Err(RecvTimeoutError::Disconnected) => return Some(set),
        }
    }
}

/// Distinct paths sorted, each with its final state: `Deleted` when the path
/// no longer exists, else `Added` if any raw event added it, else `Modified`.
/// An editor's atomic-save `deleted + added` pair becomes one `Added`.
pub fn coalesce(raw: &[RawEvent]) -> Vec<RawEvent> {
    let mut added: BTreeMap<&Path, bool> = BTreeMap::new();
    for event in raw {
        *added.entry(&event.path).or_default() |= event.kind == ChangeKind::Added;
    }
    added
        .into_iter()
        .map(|(path, was_added)| RawEvent {
            kind: if !path.exists() {
                ChangeKind::Deleted
            } else if was_added {
                ChangeKind::Added
            } else {
                ChangeKind::Modified
            },
            path: path.to_path_buf(),
        })
        .collect()
}

/// `notify`'s kind hierarchy folded onto the three kinds; access events are
/// dropped. `coalesce` re-derives the final state from disk anyway.
fn change_kind(kind: &EventKind) -> Option<ChangeKind> {
    Some(match kind {
        EventKind::Create(_) => ChangeKind::Added,
        EventKind::Remove(_) => ChangeKind::Deleted,
        EventKind::Modify(ModifyKind::Name(RenameMode::From)) => ChangeKind::Deleted,
        EventKind::Modify(ModifyKind::Name(RenameMode::To)) => ChangeKind::Added,
        EventKind::Access(_) => return None,
        _ => ChangeKind::Modified,
    })
}

/// Recursive `notify` watches on `roots`; events arrive on the returned
/// channel. Dropping the watcher closes the channel and ends the loop.
pub fn watch(
    roots: &[PathBuf],
) -> Result<(notify::RecommendedWatcher, Receiver<RawEvent>), WatchError> {
    let (tx, rx): (Sender<RawEvent>, Receiver<RawEvent>) = mpsc::channel();
    let mut watcher = notify::recommended_watcher(move |result: notify::Result<notify::Event>| {
        // A backend error means the watch is no longer complete; silence
        // here left `folio serve` claiming to watch while nothing rebuilt.
        let event = match result {
            Ok(event) => event,
            Err(error) => {
                eprintln!("warning: file watcher: {error}");
                return;
            }
        };
        let kinds: Vec<ChangeKind> = match (&event.kind, event.paths.len()) {
            // One `Both` rename event carries [from, to].
            (EventKind::Modify(ModifyKind::Name(RenameMode::Both)), 2) => {
                vec![ChangeKind::Deleted, ChangeKind::Added]
            }
            (kind, n) => match change_kind(kind) {
                Some(kind) => vec![kind; n],
                None => return,
            },
        };
        for (path, kind) in event.paths.into_iter().zip(kinds) {
            let _ = tx.send(RawEvent { kind, path });
        }
    })
    .map_err(|e| WatchError::Notify(e.to_string()))?;
    for root in roots {
        watcher
            .watch(root, RecursiveMode::Recursive)
            .map_err(|e| WatchError::Notify(format!("{}: {e}", root.display())))?;
    }
    Ok((watcher, rx))
}

#[cfg(test)]
#[path = "events_tests.rs"]
mod tests;
