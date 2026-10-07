use super::*;
use std::fs;

fn write(path: &Path, content: &str) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, content).unwrap();
}

fn names(files: &[SourceFile]) -> Vec<&str> {
    files.iter().map(|f| f.module_name.as_str()).collect()
}

#[test]
fn test_is_python_import_root() {
    let dir = tempfile::tempdir().unwrap();
    let src = dir.path().join("src");
    fs::create_dir(&src).unwrap();
    assert!(is_import_root(&src));
    write(&src.join("__init__.py"), "");
    assert!(!is_import_root(&src));
    assert!(!is_import_root(&dir.path().join("pkg")));
}

#[test]
fn test_python_path_name_matches_pathlib() {
    assert_eq!(python_path_name(Path::new("/tmp/pkg")), "pkg");
    assert_eq!(python_path_name(Path::new("/tmp/pkg/")), "pkg");
    assert_eq!(python_path_name(Path::new("/tmp/pkg/sub/..")), "..");
    assert_eq!(python_path_name(Path::new("..")), "..");
    assert_eq!(python_path_name(Path::new("/")), "");
}

#[test]
fn test_module_name_rule() {
    let root = Path::new("/proj/mypkg");
    assert_eq!(module_name(&root.join("__init__.py"), root), "mypkg");
    assert_eq!(
        module_name(&root.join("sub/deep.py"), root),
        "mypkg.sub.deep"
    );
    assert_eq!(
        module_name(&root.join("sub/__init__.py"), root),
        "mypkg.sub"
    );
    assert_eq!(module_name(&root.join("a/x.py"), root), "mypkg.a.x");
    // An import root has no prefix.
    let dir = tempfile::tempdir().unwrap();
    let src = dir.path().join("src");
    write(&src.join("acme/api.py"), "");
    assert_eq!(module_name(&src.join("acme/api.py"), &src), "acme.api");
    assert_eq!(module_name(&src.join("standalone.py"), &src), "standalone");
    assert_eq!(module_name(&src.join("acme/__init__.py"), &src), "acme");
}

#[test]
fn test_root_ending_in_dotdot_uses_pathlib_name() {
    let dir = tempfile::tempdir().unwrap();
    let pkg = dir.path().join("pkg");
    write(&pkg.join("__init__.py"), "");
    write(&pkg.join("mod_a.py"), "x = 1");
    write(&pkg.join("sub/__init__.py"), "");
    let root = PathBuf::from(format!("{}/sub/..", pkg.display()));
    let files = discover(std::slice::from_ref(&root), &[]);
    assert_eq!(names(&files), ["..", "...mod_a", "...sub"]);
    assert!(files.iter().all(|f| f.root == root));
    assert_eq!(module_name(&files[1].path, &root), "...mod_a");
}

#[test]
fn test_package_mode_discovery() {
    let dir = tempfile::tempdir().unwrap();
    let pkg = dir.path().join("mypkg");
    write(&pkg.join("__init__.py"), "");
    write(&pkg.join("mod_a.py"), "print('a')");
    write(&pkg.join("sub/__init__.py"), "");
    write(&pkg.join("sub/mod_b.py"), "print('b')");
    write(&pkg.join("nsp/leaf.py"), "");
    let files = discover(std::slice::from_ref(&pkg), &[]);
    assert_eq!(
        names(&files),
        [
            "mypkg",
            "mypkg.mod_a",
            "mypkg.nsp.leaf",
            "mypkg.sub",
            "mypkg.sub.mod_b"
        ]
    );
    assert_eq!(files[1].path, pkg.join("mod_a.py"));
    for f in &files {
        assert_eq!(module_name(&f.path, &f.root), f.module_name);
    }
}

#[test]
fn test_import_root_mode_discovery() {
    let dir = tempfile::tempdir().unwrap();
    let src = dir.path().join("src");
    write(&src.join("standalone.py"), "print('s')");
    write(&src.join("__init__.py"), "");
    fs::remove_file(src.join("__init__.py")).unwrap();
    write(&src.join("acme/__init__.py"), "");
    write(&src.join("acme/api.py"), "def ping(): pass\n");
    write(
        &src.join("extensions/payments/client.py"),
        "def charge(): pass\n",
    );
    write(&src.join("empty_dir/readme.txt"), "");
    let files = discover(std::slice::from_ref(&src), &[]);
    assert_eq!(
        names(&files),
        [
            "standalone",
            "acme",
            "acme.api",
            "extensions.payments.client"
        ]
    );
    for f in &files {
        assert_eq!(module_name(&f.path, &f.root), f.module_name);
    }
}

#[test]
fn test_missing_roots_are_skipped() {
    let dir = tempfile::tempdir().unwrap();
    assert!(discover(&[dir.path().join("missing")], &[]).is_empty());
}

#[test]
fn test_excludes_apply_per_file() {
    let dir = tempfile::tempdir().unwrap();
    let pkg = dir.path().join("pkg");
    write(&pkg.join("__init__.py"), "");
    write(&pkg.join("keep.py"), "keep");
    write(&pkg.join("__pycache__/skip.py"), "skip");
    write(&pkg.join("tests/__init__.py"), "");
    write(&pkg.join("tests/test_core.py"), "def test_it(): pass\n");
    let excludes = vec![
        "*/__pycache__/*".to_string(),
        pkg.join("tests").to_string_lossy().to_string(),
    ];
    assert_eq!(
        names(&discover(std::slice::from_ref(&pkg), &excludes)),
        ["pkg", "pkg.keep"]
    );
    // In import-root mode a package whose every file is excluded disappears.
    let src = dir.path().canonicalize().unwrap().join("src");
    write(&src.join("only/mod.py"), "");
    write(&src.join("kept/mod.py"), "");
    let excludes = vec![format!("{}/only/*", src.display())];
    assert_eq!(names(&discover(&[src], &excludes)), ["kept.mod"]);
}
