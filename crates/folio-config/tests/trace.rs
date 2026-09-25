//! The `FOLIO_TRACE` JSONL writer against a real file.

use std::fs;
use std::path::Path;

use folio_config::trace::{Tracer, TRACE_ENV_VAR};
use serde_json::{json, Value};

fn lines(path: &Path) -> Vec<Value> {
    fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}

#[test]
fn trace_appends_one_json_line_per_event_with_the_python_fields() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("nested/dir/trace.jsonl");
    let tracer = Tracer::open(&path).unwrap();
    assert_eq!(tracer.path(), path);
    tracer.trace("batch_start", &[("n_paths", json!(3))]);
    tracer.trace(
        "file_write",
        &[("path", json!("/abs/index.mdx")), ("bytes", json!(1024))],
    );
    tracer.trace("batch_start", &[]);

    let records = lines(&path);
    assert_eq!(records.len(), 3);
    let keys: Vec<&String> = records[0].as_object().unwrap().keys().collect();
    assert_eq!(keys, ["event", "t_ns", "wall_ms", "batch", "n_paths"]);
    assert_eq!(records[0]["event"], "batch_start");
    assert_eq!(records[0]["batch"], 1);
    assert_eq!(records[0]["n_paths"], 3);
    assert_eq!(records[1]["event"], "file_write");
    assert_eq!(records[1]["batch"], 1);
    assert_eq!(records[1]["path"], "/abs/index.mdx");
    assert_eq!(records[1]["bytes"], 1024);
    assert_eq!(records[2]["batch"], 2);
    let t: Vec<u64> = records
        .iter()
        .map(|r| r["t_ns"].as_u64().unwrap())
        .collect();
    assert!(t[0] <= t[1] && t[1] <= t[2]);
    let wall = records[0]["wall_ms"].as_f64().unwrap();
    assert!(wall > 1.7e12, "epoch milliseconds, got {wall}");

    // A second tracer appends; the batch counter is per tracer.
    let again = Tracer::open(&path).unwrap();
    again.trace("manifest_saved", &[]);
    let records = lines(&path);
    assert_eq!(records.len(), 4);
    assert_eq!(records[3]["batch"], 0);
}

#[test]
fn unwritable_path_is_the_python_warning() {
    let dir = tempfile::tempdir().unwrap();
    let blocker = dir.path().join("file");
    fs::write(&blocker, "").unwrap();
    let path = blocker.join("trace.jsonl");
    let err = Tracer::open(&path).unwrap_err();
    assert!(
        err.starts_with(&format!("FOLIO_TRACE: cannot open {}: ", path.display())),
        "{err}"
    );
    assert!(err.ends_with("; tracing disabled"), "{err}");
}

#[test]
fn from_env_is_none_unless_the_variable_names_a_path() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("t.jsonl");
    std::env::set_var(TRACE_ENV_VAR, path.to_string_lossy().as_ref());
    let tracer = Tracer::from_env().unwrap().expect("enabled");
    assert_eq!(tracer.path(), path);
    std::env::set_var(TRACE_ENV_VAR, "   ");
    assert!(Tracer::from_env().unwrap().is_none());
    std::env::remove_var(TRACE_ENV_VAR);
    assert!(Tracer::from_env().unwrap().is_none());
}
