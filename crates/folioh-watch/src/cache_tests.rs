use super::*;

fn p(s: &str) -> PathBuf {
    PathBuf::from(s)
}

#[test]
fn upsert_replaces_by_path_and_remove_drops_it() {
    let mut cache: RetainedCache<&str> = RetainedCache::default();
    cache.upsert(p("/p/a.py"), "h1", "A");
    cache.upsert(p("/p/b.py"), "h2", "B");
    cache.upsert(p("/p/a.py"), "h3", "A2");
    assert_eq!(cache.len(), 2);
    assert_eq!(
        cache.get(Path::new("/p/a.py")),
        Some(&Entry {
            hash: "h3".into(),
            payload: "A2"
        })
    );
    assert_eq!(cache.payloads().collect::<Vec<_>>(), vec![&"A2", &"B"]);
    cache.remove(Path::new("/p/a.py"));
    assert_eq!(cache.get(Path::new("/p/a.py")), None);
    assert_eq!(
        cache.paths().collect::<Vec<_>>(),
        vec![Path::new("/p/b.py")]
    );
    assert!(!cache.is_empty());
}

#[test]
fn stale_entries_are_the_ones_whose_hash_moved() {
    let mut cache: RetainedCache<()> = RetainedCache::default();
    cache.upsert(p("/p/a.py"), "h1", ());
    cache.upsert(p("/p/b.py"), "h2", ());
    let stale = cache.stale(|path| {
        if path.ends_with("a.py") {
            "changed".into()
        } else {
            "h2".into()
        }
    });
    assert_eq!(stale, vec![p("/p/a.py")]);
}
