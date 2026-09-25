use super::*;

#[test]
fn relpath_walks_up_and_down() {
    assert_eq!(
        relpath(Path::new("/a/b/c"), Path::new("/a/b")),
        PathBuf::from("c")
    );
    assert_eq!(
        relpath(Path::new("/a/x"), Path::new("/a/b/c")),
        PathBuf::from("../../x")
    );
    assert_eq!(
        relpath(Path::new("/a/b"), Path::new("/a/b")),
        PathBuf::new()
    );
}

#[test]
fn shlex_quote_matches_python() {
    assert_eq!(
        shlex_quote("tmp/sample-init-check"),
        "tmp/sample-init-check"
    );
    assert_eq!(shlex_quote("my project"), "'my project'");
    assert_eq!(shlex_quote("it's"), "'it'\"'\"'s'");
    assert_eq!(shlex_quote(""), "''");
}

#[test]
fn cli_paths_are_cwd_relative_and_the_cwd_is_a_dot() {
    let here = env::current_dir().unwrap();
    assert_eq!(format_cli_path(&here), ".");
    assert_eq!(command_target_suffix(&here), "");
    assert_eq!(format_cli_path(&here.join("tmp/x y")), "tmp/x y");
    assert_eq!(command_target_suffix(&here.join("tmp/x y")), " 'tmp/x y'");
    assert_eq!(format_cli_path(&here.join("../zz")), "../zz");
}

#[test]
fn resolve_path_keeps_a_missing_tail() {
    let dir = tempfile::tempdir().unwrap();
    let real = dir.path().canonicalize().unwrap();
    assert_eq!(
        resolve_path(&dir.path().join("missing/deep")),
        real.join("missing/deep")
    );
    assert_eq!(resolve_path(dir.path()), real);
    assert_eq!(
        resolve_path(&dir.path().join("a/../..")),
        real.parent().unwrap()
    );
    assert_eq!(resolve_path(&dir.path().join("./x/./y")), real.join("x/y"));
}

#[test]
fn conflicting_project_directories_are_an_error() {
    let dir = tempfile::tempdir().unwrap();
    let a = dir.path().join("a");
    let b = dir.path().join("b");
    std::fs::create_dir_all(&a).unwrap();
    std::fs::create_dir_all(&b).unwrap();
    let both = ProjectArgs {
        directory: Some(a.clone()),
        project_dir: Some(b),
    };
    let err = both.resolve().unwrap_err();
    assert_eq!(
        err.to_string(),
        "Error: Pass the project directory either as an argument or --project-dir, not both."
    );
    let same = ProjectArgs {
        directory: Some(a.clone()),
        project_dir: Some(a.clone()),
    };
    assert_eq!(same.resolve().unwrap(), a.canonicalize().unwrap());
    let one = ProjectArgs {
        directory: None,
        project_dir: Some(a.clone()),
    };
    assert_eq!(one.resolve().unwrap(), a.canonicalize().unwrap());
}
