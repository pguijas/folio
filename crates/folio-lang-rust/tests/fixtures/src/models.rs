//! Data models for the demo crate.

use std::fmt;

/// A 2D point with named fields.
#[derive(Debug, Clone)]
pub struct Point {
    /// The x coordinate.
    pub x: f64,
    /// The y coordinate.
    pub y: f64,
}

/// A tuple struct wrapping an ID.
pub struct Id(pub u64);

/// A unit struct used as a marker.
pub struct Marker;

/// A generic container.
pub struct Container<T: Clone> {
    /// The inner value.
    pub value: T,
}

/// Directions on a compass.
pub enum Direction {
    /// Points north.
    North,
    /// Points south.
    South,
    /// Points east with a bearing.
    East(f64),
    /// Points west with coordinates.
    West { lat: f64, lon: f64 },
}

/// Errors that can occur.
#[repr(u8)]
pub enum ErrorCode {
    /// Not found.
    NotFound = 1,
    /// Permission denied.
    Denied = 2,
}

/// A trait for objects that can be displayed as a summary.
pub trait Summary {
    /// The associated output type.
    type Output;

    /// Required: produce a summary string.
    fn summarize(&self) -> Self::Output;

    /// Provided: produce a default summary.
    fn default_summary(&self) -> String {
        String::from("(no summary)")
    }
}

/// An async-safe trait.
pub trait AsyncProcess {
    /// An associated constant for timeout.
    const TIMEOUT: u64;

    /// Run the process.
    fn run(&self);
}

impl Point {
    /// Create a new point.
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Distance from the origin.
    pub fn distance(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }

    /// A private method (should be skipped).
    fn validate(&self) -> bool {
        true
    }
}

impl Summary for Point {
    type Output = String;

    fn summarize(&self) -> String {
        format!("({}, {})", self.x, self.y)
    }
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

/// A type alias for results.
pub type Result<T> = std::result::Result<T, ErrorCode>;

/// A `pub(crate)` function for internal use (should be skipped).
pub(crate) fn helper() -> bool {
    true
}

/// A `pub(super)` function (should be skipped).
pub(super) fn parent_visible() -> bool {
    true
}

/// An unsafe function.
pub unsafe fn dangerous() {}

/// An async function.
pub async fn fetch_data(url: &str) -> Result<String> {
    Ok(url.to_string())
}

/// A const function.
pub const fn max_size() -> usize {
    1024
}

/// A function with generics and where clause.
pub fn process<T, U>(input: T) -> U
where
    T: Clone + fmt::Debug,
    U: Default,
{
    U::default()
}

/// An attribute-bearing function.
#[cfg(feature = "extra")]
pub fn conditional() {}

/// A macro invocation at item level (listed as unsupported).
macro_rules! define_id {
    ($name:ident) => {
        pub struct $name(u64);
    };
}

define_id!(UserId);

/// A re-export.
pub use std::collections::HashMap;
