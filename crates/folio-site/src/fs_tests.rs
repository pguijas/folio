use super::*;

#[test]
fn write_text_if_changed_creates_file_with_default_mode_and_skips_identical() {
    let dir = tempfile::tempdir().unwrap();
    let target = dir.path().join("nested").join("generated.txt");
    assert!(write_text_if_changed(&target, "generated\n").unwrap());
    assert_eq!(std::fs::read_to_string(&target).unwrap(), "generated\n");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        assert_eq!(
            std::fs::metadata(&target).unwrap().permissions().mode() & 0o777,
            0o644
        );
    }
    let before = std::fs::metadata(&target).unwrap().modified().unwrap();
    assert!(!write_text_if_changed(&target, "generated\n").unwrap());
    assert_eq!(
        std::fs::metadata(&target).unwrap().modified().unwrap(),
        before
    );
    assert_eq!(
        std::fs::read_dir(target.parent().unwrap()).unwrap().count(),
        1
    );
}

#[cfg(unix)]
#[test]
fn write_text_if_changed_preserves_existing_mode() {
    use std::os::unix::fs::PermissionsExt;
    let dir = tempfile::tempdir().unwrap();
    let target = dir.path().join("generated.txt");
    std::fs::write(&target, "old\n").unwrap();
    std::fs::set_permissions(&target, std::fs::Permissions::from_mode(0o640)).unwrap();
    assert!(write_text_if_changed(&target, "new\n").unwrap());
    assert_eq!(std::fs::read_to_string(&target).unwrap(), "new\n");
    assert_eq!(
        std::fs::metadata(&target).unwrap().permissions().mode() & 0o777,
        0o640
    );
}

#[cfg(unix)]
#[test]
fn write_text_if_changed_failure_keeps_original_and_no_temp_file() {
    use std::os::unix::fs::PermissionsExt;
    let dir = tempfile::tempdir().unwrap();
    let sub = dir.path().join("locked");
    std::fs::create_dir(&sub).unwrap();
    let target = sub.join("generated.txt");
    std::fs::write(&target, "old\n").unwrap();
    std::fs::set_permissions(&sub, std::fs::Permissions::from_mode(0o555)).unwrap();
    let result = write_text_if_changed(&target, "new\n");
    std::fs::set_permissions(&sub, std::fs::Permissions::from_mode(0o755)).unwrap();
    assert!(result.is_err());
    assert_eq!(std::fs::read_to_string(&target).unwrap(), "old\n");
    let names: Vec<_> = std::fs::read_dir(&sub)
        .unwrap()
        .map(|e| e.unwrap().file_name())
        .collect();
    assert_eq!(names, vec![std::ffi::OsString::from("generated.txt")]);
}

#[test]
fn copy_tree_skips_ignored_dirs_and_root_injected_files() {
    let dir = tempfile::tempdir().unwrap();
    let src = dir.path().join("src");
    for rel in [
        "app/layout.tsx",
        "content/index.mdx",
        "node_modules/x.js",
        "next.config.mjs",
        "deep/node_modules/y.js",
        "deep/next.config.mjs",
        ".folio-staging",
    ] {
        let path = src.join(rel);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(&path, rel).unwrap();
    }
    let dst = dir.path().join("dst");
    copy_tree(&src, &dst, &INJECTED_ROOT_FILES).unwrap();
    assert!(dst.join("app/layout.tsx").is_file());
    assert!(dst.join("deep/next.config.mjs").is_file());
    for absent in [
        "content",
        "node_modules",
        "next.config.mjs",
        "deep/node_modules",
        ".folio-staging",
    ] {
        assert!(!dst.join(absent).exists(), "{absent} copied");
    }
    let walked: Vec<String> = walk_copied_entries(&src)
        .iter()
        .map(|p| posix(p.strip_prefix(&src).unwrap()))
        .collect();
    assert!(walked.contains(&"app/layout.tsx".to_string()));
    assert!(!walked
        .iter()
        .any(|p| p.starts_with("node_modules") || p.starts_with("content")));
}

#[cfg(unix)]
#[test]
fn reject_symlinks_names_the_relative_entry_and_ignores_pruned_dirs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().join("pkg");
    std::fs::create_dir_all(root.join("node_modules")).unwrap();
    std::fs::write(root.join("a.txt"), "a").unwrap();
    std::os::unix::fs::symlink("/etc/hosts", root.join("node_modules/hosts")).unwrap();
    assert!(reject_symlinks(&root, "theme.package").is_ok());
    std::fs::create_dir_all(root.join("app")).unwrap();
    std::os::unix::fs::symlink(root.join("a.txt"), root.join("app/link.txt")).unwrap();
    let err = reject_symlinks(&root, "theme.package").unwrap_err();
    assert_eq!(
        err.to_string(),
        "theme.package must not contain symlinks: app/link.txt"
    );
    assert_eq!(
        collect_copyable_files(&root, "theme.package")
            .unwrap_err()
            .to_string(),
        "theme.package must not contain symlinks: app/link.txt"
    );
}

#[test]
fn hash_tree_is_stable_and_skips_build_residue() {
    let dir = tempfile::tempdir().unwrap();
    std::fs::create_dir_all(dir.path().join("a/node_modules")).unwrap();
    std::fs::write(dir.path().join("a/x.txt"), "x").unwrap();
    let first = hash_tree(dir.path());
    std::fs::write(dir.path().join("a/node_modules/y.txt"), "y").unwrap();
    std::fs::create_dir_all(dir.path().join("out")).unwrap();
    std::fs::write(dir.path().join("out/z.txt"), "z").unwrap();
    assert_eq!(hash_tree(dir.path()), first);
    std::fs::write(dir.path().join("a/x.txt"), "changed").unwrap();
    assert_ne!(hash_tree(dir.path()), first);
    assert_eq!(hash_file(&dir.path().join("missing")), "");
    assert_eq!(
        hash_file(&dir.path().join("a/x.txt")),
        sha256_hex(b"changed")
    );
}
