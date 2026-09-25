//! The real OS watcher on a temp dir: create, modify, remove one file.
//! Set `FOLIO_WATCH_SKIP_NOTIFY_SMOKE=1` to skip it on a flaky CI runner.

use std::path::Path;
use std::time::{Duration, Instant};

use folio_watch::{coalesce, collect_set, watch, ChangeKind, Debounce};

/// Collect debounced sets until `done` accepts the coalesced kinds seen for
/// `file`, or the deadline passes.
fn wait_for(
    rx: &std::sync::mpsc::Receiver<folio_watch::RawEvent>,
    file: &Path,
    done: impl Fn(&[ChangeKind]) -> bool,
) -> Vec<ChangeKind> {
    let deadline = Instant::now() + Duration::from_secs(8);
    let mut seen = Vec::new();
    let debounce = Debounce {
        quiet: Duration::from_millis(50),
        cap: Duration::from_millis(400),
    };
    while Instant::now() < deadline && !done(&seen) {
        let Some(set) = collect_set(rx, debounce) else {
            break;
        };
        for event in coalesce(&set) {
            if event.path.file_name() == file.file_name() && !seen.contains(&event.kind) {
                seen.push(event.kind);
            }
        }
    }
    seen
}

#[test]
fn create_modify_remove_reach_the_channel() {
    if std::env::var_os("FOLIO_WATCH_SKIP_NOTIFY_SMOKE").is_some() {
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    let (watcher, rx) = watch(std::slice::from_ref(&root)).unwrap();
    // FSEvents needs a moment before it reports on a fresh watch.
    std::thread::sleep(Duration::from_millis(300));

    let file = root.join("note.md");
    std::fs::write(&file, "one").unwrap();
    let seen = wait_for(&rx, &file, |s| !s.is_empty());
    assert!(
        seen.contains(&ChangeKind::Added) || seen.contains(&ChangeKind::Modified),
        "create not seen: {seen:?}"
    );

    std::fs::write(&file, "two").unwrap();
    let seen = wait_for(&rx, &file, |s| !s.is_empty());
    assert!(!seen.is_empty(), "modify not seen");

    std::fs::remove_file(&file).unwrap();
    let seen = wait_for(&rx, &file, |s| s.contains(&ChangeKind::Deleted));
    assert!(
        seen.contains(&ChangeKind::Deleted),
        "remove not seen: {seen:?}"
    );

    drop(watcher);
    assert!(
        collect_set(&rx, Debounce::default()).is_none(),
        "dropping the watcher closes the channel"
    );
}
