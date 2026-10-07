//! JSON rendering in the shapes Python's `json.dumps` produced: compact with
//! `", "`/`": "` separators, and `indent=2`. UTF-8 throughout, never `\uXXXX`.

use std::io;

use serde::Serialize;
use serde_json::ser::Formatter;

struct PyCompact;

impl Formatter for PyCompact {
    fn begin_array_value<W: ?Sized + io::Write>(
        &mut self,
        writer: &mut W,
        first: bool,
    ) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ")
        }
    }
    fn begin_object_key<W: ?Sized + io::Write>(
        &mut self,
        writer: &mut W,
        first: bool,
    ) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ")
        }
    }
    fn begin_object_value<W: ?Sized + io::Write>(&mut self, writer: &mut W) -> io::Result<()> {
        writer.write_all(b": ")
    }
}

/// `json.dumps(value)`: one line, `", "` and `": "` separators.
pub fn compact<T: Serialize>(value: &T) -> String {
    let mut out = Vec::new();
    let mut ser = serde_json::Serializer::with_formatter(&mut out, PyCompact);
    value.serialize(&mut ser).expect("serialisable value");
    String::from_utf8(out).expect("utf-8 json")
}

/// `json.dumps(value, indent=2)`.
pub fn pretty<T: Serialize>(value: &T) -> String {
    serde_json::to_string_pretty(value).expect("serialisable value")
}

/// `json.dumps(text)`: a quoted JSON string literal.
pub fn string(text: &str) -> String {
    serde_json::to_string(text).expect("string")
}

#[cfg(test)]
#[path = "json_tests.rs"]
mod tests;
