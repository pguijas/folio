use super::*;
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

fn ev(kind: ChangeKind, path: &Path) -> RawEvent {
    RawEvent {
        kind,
        path: path.to_path_buf(),
    }
}

#[test]
fn coalesce_sorts_paths_and_keeps_the_final_state() {
    let dir = tempfile::tempdir().unwrap();
    let readme = dir.path().join("README.md");
    let added = dir.path().join("added.md");
    let touched = dir.path().join("touched.py");
    let gone = dir.path().join("gone.md");
    for p in [&readme, &added, &touched] {
        std::fs::write(p, "x").unwrap();
    }
    let raw = vec![
        ev(ChangeKind::Modified, &touched),
        ev(ChangeKind::Deleted, &readme),
        ev(ChangeKind::Added, &readme),
        ev(ChangeKind::Added, &added),
        ev(ChangeKind::Modified, &readme),
        ev(ChangeKind::Added, &gone),
        ev(ChangeKind::Added, &added),
    ];
    let out = coalesce(&raw);
    assert_eq!(
        out,
        vec![
            ev(ChangeKind::Added, &readme),
            ev(ChangeKind::Added, &added),
            ev(ChangeKind::Deleted, &gone),
            ev(ChangeKind::Modified, &touched),
        ]
    );
}

#[test]
fn notify_kinds_map_to_the_three_change_kinds() {
    use notify::event::{CreateKind, DataChange, ModifyKind, RemoveKind, RenameMode};
    use notify::EventKind;
    assert_eq!(
        change_kind(&EventKind::Create(CreateKind::File)),
        Some(ChangeKind::Added)
    );
    assert_eq!(
        change_kind(&EventKind::Remove(RemoveKind::Any)),
        Some(ChangeKind::Deleted)
    );
    assert_eq!(
        change_kind(&EventKind::Modify(ModifyKind::Data(DataChange::Content))),
        Some(ChangeKind::Modified)
    );
    assert_eq!(
        change_kind(&EventKind::Modify(ModifyKind::Name(RenameMode::From))),
        Some(ChangeKind::Deleted)
    );
    assert_eq!(
        change_kind(&EventKind::Modify(ModifyKind::Name(RenameMode::To))),
        Some(ChangeKind::Added)
    );
    assert_eq!(change_kind(&EventKind::Any), Some(ChangeKind::Modified));
    assert_eq!(
        change_kind(&EventKind::Access(notify::event::AccessKind::Any)),
        None
    );
}

const FAST: Debounce = Debounce {
    quiet: Duration::from_millis(40),
    cap: Duration::from_millis(150),
};

#[test]
fn a_burst_inside_the_quiet_window_is_one_set() {
    let (tx, rx) = mpsc::channel();
    for i in 0..3 {
        tx.send(ev(ChangeKind::Modified, Path::new(&format!("/p/{i}.md"))))
            .unwrap();
    }
    let set = collect_set(&rx, FAST).unwrap();
    assert_eq!(set.len(), 3);
    // Nothing else pending; the source closing ends the stream.
    drop(tx);
    assert!(collect_set(&rx, FAST).is_none());
}

#[test]
fn a_quiet_gap_splits_two_sets() {
    let (tx, rx) = mpsc::channel();
    tx.send(ev(ChangeKind::Added, Path::new("/p/a.md")))
        .unwrap();
    thread::spawn(move || {
        thread::sleep(FAST.quiet * 3);
        tx.send(ev(ChangeKind::Added, Path::new("/p/b.md")))
            .unwrap();
    });
    assert_eq!(collect_set(&rx, FAST).unwrap().len(), 1);
    assert_eq!(collect_set(&rx, FAST).unwrap().len(), 1);
}

#[test]
fn a_continuous_stream_is_cut_at_the_cap() {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        for i in 0..200 {
            if tx
                .send(ev(ChangeKind::Modified, Path::new(&format!("/p/{i}.md"))))
                .is_err()
            {
                return;
            }
            thread::sleep(Duration::from_millis(5));
        }
    });
    let started = Instant::now();
    let set = collect_set(&rx, FAST).unwrap();
    let took = started.elapsed();
    assert!(set.len() > 3, "got {} events", set.len());
    assert!(took >= FAST.cap, "cut too early: {took:?}");
    assert!(
        took < FAST.cap * 3,
        "quiet window never came, but the cap did not cut: {took:?}"
    );
    drop(rx);
}
