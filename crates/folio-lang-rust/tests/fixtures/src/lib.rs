//! The demo crate for testing Folio's Rust source support.
//!
//! This crate exercises every documented surface.

pub mod models;
pub mod utils;

/// A top-level public function.
///
/// # Examples
///
/// ```
/// # use demo::init;
/// assert!(init("demo"));
/// ```
///
/// Returns what [`models::Config`] reads, see [the utils][utils].
///
/// [utils]: crate::utils
pub fn init(name: &str) -> bool {
    !name.is_empty()
}

/// A private function (should be skipped).
fn internal_setup() {}

/// A constant at the crate root.
pub const VERSION: &str = "0.1.0";

/// A static mutable counter.
pub static COUNTER: std::sync::atomic::AtomicUsize =
    std::sync::atomic::AtomicUsize::new(0);
