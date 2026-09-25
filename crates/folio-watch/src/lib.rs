//! The watcher behind `folio serve`: watched roots, the ignore filter, event
//! coalescing, the batch loop, the retained cache and the trace events. It
//! knows nothing about IR or MDX; the binary's `BatchHandler` does the work.

pub mod batch;
pub mod cache;
pub mod events;
pub mod filter;

pub use batch::{run_loop, BatchHandler, BatchSummary, Event};
pub use cache::{Entry, RetainedCache};
pub use events::{coalesce, collect_set, watch, ChangeKind, Debounce, RawEvent};
pub use filter::{
    default_ignore, is_under, with_preview_examples, Batch, LanguageRoots, WatchConfig,
};

/// The one error this crate raises itself; handler errors are plain strings.
#[derive(Debug, thiserror::Error)]
pub enum WatchError {
    /// The OS watcher could not be created or a root could not be watched.
    #[error("cannot watch for file changes: {0}")]
    Notify(String),
}
