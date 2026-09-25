use super::*;

fn check(candidate: &str, pattern: &str, expected: bool) {
    assert_eq!(
        fnmatch(candidate, pattern),
        expected,
        "fnmatch({candidate:?}, {pattern:?}) should be {expected}"
    );
}

#[test]
fn test_fnmatch_table() {
    // basic star
    check("abc", "*", true);
    check("", "*", true);
    check("abc", "ab*", true);
    check("abc", "*bc", true);
    check("abc", "*b*", true);
    // question mark
    check("a", "?", true);
    check("ab", "??", true);
    check("abc", "?", false);
    check("abc", "???", true);
    check("abc", "????", false);
    // brackets and ranges
    check("a", "[abc]", true);
    check("d", "[abc]", false);
    check("a", "[!abc]", false);
    check("d", "[!abc]", true);
    check("b", "[a-c]", true);
    check("d", "[a-c]", false);
    check("B", "[a-c]", false);
    // star crosses slashes
    check("/foo/bar/baz", "*baz", true);
    check("/foo/bar/baz", "*/baz", true);
    check("/foo/bar/baz", "*bar*", true);
    check("/foo/bar/baz", "/foo/*/baz", true);
    // exact
    check("foo", "foo", true);
    check("foo", "bar", false);
    // ** is just two stars
    check("foo/bar/baz", "foo/**/baz", true);
    check("foo/baz", "foo/**/baz", false);
    // documented patterns
    check("foo.py", "*.py", true);
    check("foo.txt", "*.py", false);
    check("a/b/c/__pycache__/d.pyc", "*/__pycache__/*", true);
    check("skip_test.py", "**/skip_*.py", false);
    check("/usr/local/skip_abc.py", "**/skip_*.py", true);
    // negation, empty pattern, only stars, ? with *
    check("x", "[!a]", true);
    check("a", "[!a]", false);
    check("", "", true);
    check("a", "", false);
    check("anything/here", "***", true);
    check("ab", "?*", true);
    check("a", "?*", true);
    check("", "?*", false);
}

#[test]
fn test_fnmatch_reversed_range_is_dropped() {
    // CPython: fnmatch.translate("[c-a]") never matches.
    check("a", "[c-a]", false);
    check("b", "[c-a]", false);
    check("c", "[c-a]", false);
    // Other members survive the removal: "[xc-ay]" -> "[xy]".
    check("x", "[xc-ay]", true);
    check("y", "[xc-ay]", true);
    check("b", "[xc-ay]", false);
    // A literal hyphen right after a range end: "[a-c-e]" -> a-c, '-', 'e'.
    check("-", "[a-c-e]", true);
    check("e", "[a-c-e]", true);
    check("d", "[a-c-e]", false);
    // Trailing hyphen is literal.
    check("-", "[a-]", true);
    check("b", "[a-]", false);
}

#[test]
fn test_fnmatch_caret_is_literal_only_bang_negates() {
    check("^", "[^a]", true);
    check("a", "[^a]", true);
    check("b", "[^a]", false);
    check("a", "[!a]", false);
    check("b", "[!a]", true);
}

#[test]
fn test_fnmatch_bracket_edge_cases() {
    check("]", "[]]", true);
    check("a", "[]a]", true);
    check("a", "[]-a]", true);
    check("b", "[]-a]", false);
    check("[a", "[a", true);
    check("a", "[a", false);
    check("[!]", "[!]", true);
    check("!", "[!]", false);
    check("x", "[!]]", true);
    check("]", "[!]]", false);
}

#[test]
fn test_fnmatch_matches_chars_not_bytes() {
    check("é", "?", true);
    check("é", "??", false);
    check("日", "[一-龥]", true);
    check("é", "[é]", true);
    check("é", "[!é]", false);
    check("café.py", "caf?.py", true);
    check("caf\u{e9}.py", "caf[\u{e8}-\u{ea}].py", true);
    check("/src/日本/mod.py", "*/日本/*", true);
    check("ab", "?", false);
}

fn real_tmp() -> String {
    std::fs::canonicalize("/tmp")
        .unwrap()
        .to_string_lossy()
        .to_string()
}

#[test]
fn test_resolve_nonstrict() {
    let tmp = real_tmp();
    assert_eq!(
        resolve_nonstrict("/tmp/folio_test_nonexistent_1234/sub"),
        format!("{tmp}/folio_test_nonexistent_1234/sub")
    );
    assert_eq!(
        resolve_nonstrict("/tmp/folio_test_xyz/a/b/../c"),
        format!("{tmp}/folio_test_xyz/a/c")
    );
    assert_eq!(resolve_nonstrict("/tmp"), tmp);
    assert_eq!(resolve_nonstrict("/tmp/folio_test_xyz/.."), tmp);
}

#[cfg(unix)]
#[test]
fn test_resolve_nonstrict_symlink_chain() {
    let dir = tempfile::tempdir().unwrap();
    let real = dir.path().join("real_dir");
    std::fs::create_dir(&real).unwrap();
    let link = dir.path().join("link_dir");
    std::os::unix::fs::symlink(&real, &link).unwrap();
    let result = resolve_nonstrict(&format!("{}/subdir/file.txt", link.display()));
    let real_canon = std::fs::canonicalize(&real).unwrap();
    assert_eq!(result, format!("{}/subdir/file.txt", real_canon.display()));
}

#[test]
fn test_python_sort_order() {
    let mut paths = vec!["pkg/a.py", "pkg/a-b.py", "pkg/a/x.py", "pkg/a_b.py"];
    paths.sort_by_key(|p| python_sort_key(Path::new(p)));
    assert_eq!(
        paths,
        ["pkg/a/x.py", "pkg/a-b.py", "pkg/a.py", "pkg/a_b.py"]
    );
}

#[test]
fn test_literal_exclude_matches_on_component_boundaries() {
    // Globs compare against the resolved candidate, so an absolute glob prefix
    // must itself be the real path (config resolves project paths the same way).
    let dir = tempfile::tempdir().unwrap();
    let base = dir.path().canonicalize().unwrap();
    let dir = &base;
    let internal = dir.join("internal");
    let hidden = internal.join("hidden.py");
    let public = dir.join("internal_tools").join("public.py");
    let excludes = vec![internal.to_string_lossy().to_string()];
    assert!(is_excluded(&hidden, &excludes));
    assert!(!is_excluded(&public, &excludes));
    assert!(is_excluded(&internal, &excludes));
    // A trailing slash and a missing literal are harmless.
    let with_slash = vec![format!("{}/", internal.display())];
    assert!(is_excluded(&hidden, &with_slash));
    assert!(!is_excluded(&public, &["/nonexistent/x".to_string()]));
    // Globs match the resolved path and its subtree.
    let glob = vec![format!("{}/**/tests", dir.display())];
    assert!(is_excluded(&dir.join("pkg/tests/test_a.py"), &glob));
    assert!(!is_excluded(&dir.join("pkg/tests_extra/a.py"), &glob));
}
