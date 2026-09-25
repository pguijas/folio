//! Discovery and excludes over real directory trees.

use std::fs;
use std::path::{Path, PathBuf};

use folio_lang_python::{discover, parse_file, DocstringStyle};

fn write(path: &Path, content: &str) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, content).unwrap();
}

/// A real (symlink-free) temp dir: excludes compare resolved paths.
fn tempdir() -> (tempfile::TempDir, PathBuf) {
    let dir = tempfile::tempdir().unwrap();
    let real = dir.path().canonicalize().unwrap();
    (dir, real)
}

fn names(roots: &[PathBuf], excludes: &[String]) -> Vec<String> {
    discover(roots, excludes)
        .into_iter()
        .map(|f| f.module_name)
        .collect()
}

#[test]
fn parity_tree_discovers_in_python_order_with_every_exclude_form() {
    let (_guard, tmp) = tempdir();
    let pkg = tmp.join("mypkg");
    write(&pkg.join("__init__.py"), "# root init");
    write(&pkg.join("alpha.py"), "x = 1");
    write(&pkg.join("beta.py"), "y = 2");
    write(&pkg.join("sub/__init__.py"), "# sub init");
    write(&pkg.join("sub/deep.py"), "z = 3");
    write(&pkg.join(".hidden/x.py"), "hidden = True");
    write(&pkg.join("a/__init__.py"), "");
    write(&pkg.join("a/x.py"), "# a.x");
    write(&pkg.join("a-b.py"), "# a-b");
    write(&pkg.join("a_b.py"), "# a_b");
    #[cfg(unix)]
    {
        std::os::unix::fs::symlink(pkg.join("alpha.py"), pkg.join("link_alpha.py")).unwrap();
        let linked_dir = tmp.join("real_extra");
        write(&linked_dir.join("__init__.py"), "");
        write(&linked_dir.join("mod.py"), "# extra");
        std::os::unix::fs::symlink(&linked_dir, pkg.join("linked_pkg")).unwrap();
    }
    let src = tmp.join("src");
    write(&src.join("standalone.py"), "s = 1");
    write(&src.join("mypkg2/__init__.py"), "");
    write(&src.join("mypkg2/core.py"), "c = 1");
    write(&src.join("mypkg2/util.py"), "u = 1");
    write(&pkg.join("__pycache__/alpha.cpython-312.pyc"), "bytecode");
    write(
        &pkg.join("__pycache__/cached.py"),
        "# .py under __pycache__",
    );
    write(&pkg.join("skip_this.py"), "# should be excluded");
    write(&pkg.join("sub/te_st.py"), "# bracket pattern target");

    let excludes = vec![
        "*/__pycache__/*".to_string(),
        "**/skip_*.py".to_string(),
        tmp.join("nonexistent_exclude")
            .to_string_lossy()
            .to_string(),
        pkg.join("beta.py").to_string_lossy().to_string(),
        "*/te[_]?t.py".to_string(),
    ];
    let roots = vec![pkg.clone(), src.clone(), tmp.join("no_such_root")];
    let files = discover(&roots, &excludes);
    let mut expected = vec![
        "mypkg..hidden.x",
        "mypkg",
        "mypkg.a",
        "mypkg.a.x",
        "mypkg.a-b",
        "mypkg.a_b",
        "mypkg.alpha",
    ];
    if cfg!(unix) {
        expected.push("mypkg.link_alpha");
    }
    expected.extend([
        "mypkg.sub",
        "mypkg.sub.deep",
        "standalone",
        "mypkg2",
        "mypkg2.core",
        "mypkg2.util",
    ]);
    let got: Vec<&str> = files.iter().map(|f| f.module_name.as_str()).collect();
    assert_eq!(got, expected);
    assert!(files.iter().take(expected.len() - 4).all(|f| f.root == pkg));
    assert!(files.iter().skip(expected.len() - 4).all(|f| f.root == src));
    assert_eq!(files[1].path, pkg.join("__init__.py"));
    assert_eq!(files.last().unwrap().path, src.join("mypkg2/util.py"));
}

#[test]
fn package_root_with_literal_directory_exclude() {
    let (_guard, tmp) = tempdir();
    let pkg = tmp.join("mylib");
    write(&pkg.join("__init__.py"), "\"\"\"My library.\"\"\"\n");
    write(
        &pkg.join("core.py"),
        "def run(x: int) -> int:\n    return x\n",
    );
    assert_eq!(
        names(std::slice::from_ref(&pkg), &[]),
        ["mylib", "mylib.core"]
    );

    let tests_dir = pkg.join("tests");
    write(&tests_dir.join("__init__.py"), "");
    write(&tests_dir.join("test_core.py"), "def test_it(): pass\n");
    let excludes = vec![tests_dir.to_string_lossy().to_string()];
    assert_eq!(names(&[pkg], &excludes), ["mylib", "mylib.core"]);
}

#[test]
fn documented_exclude_globs_and_shared_prefixes() {
    let (_guard, tmp) = tempdir();
    let pkg = tmp.join("src/demo");
    write(&pkg.join("__init__.py"), "");
    write(&pkg.join("core.py"), "PUBLIC = True\n");
    write(&pkg.join("test_unit.py"), "HIDDEN = True\n");
    write(&pkg.join("tests/test_hidden.py"), "HIDDEN = True\n");
    write(&pkg.join("conftest.py"), "FIXTURE = True\n");
    let excludes = vec![
        format!("{}/**/test_*.py", tmp.display()),
        format!("{}/**/tests/", tmp.display()),
        format!("{}/**/conftest.py", tmp.display()),
    ];
    assert_eq!(names(&[pkg], &excludes), ["demo", "demo.core"]);

    let demo = tmp.join("demo");
    write(&demo.join("internal/hidden.py"), "HIDDEN = True\n");
    write(&demo.join("internal_tools/public.py"), "PUBLIC = True\n");
    let excludes = vec![demo.join("internal").to_string_lossy().to_string()];
    assert_eq!(names(&[demo], &excludes), ["demo.internal_tools.public"]);
}

#[test]
fn src_is_an_import_root_and_profiles_line_up() {
    let (_guard, tmp) = tempdir();
    let src = tmp.join("src");
    write(&src.join("acme/__init__.py"), "\"\"\"Acme package.\"\"\"\n");
    write(&src.join("acme/api.py"), "def ping(): pass\n");
    write(
        &src.join("extensions/payments/client.py"),
        "def charge(): pass\n",
    );
    write(&src.join("standalone.py"), "def run(): pass\n");
    assert_eq!(
        names(std::slice::from_ref(&src), &[]),
        [
            "standalone",
            "acme",
            "acme.api",
            "extensions.payments.client"
        ]
    );

    // test_languages: package + import root, literal file exclude, NumPy merge.
    let package = tmp.join("mylib");
    write(&package.join("__init__.py"), "\"\"\"My library.\"\"\"\n");
    write(
        &package.join("core.py"),
        "\"\"\"Core.\"\"\"\n\n\ndef run(x: int) -> int:\n    \"\"\"Run.\n\n    Parameters\n    ----------\n    x : int\n        Value.\n    \"\"\"\n    return x\n",
    );
    write(&package.join("skip.py"), "SKIPPED = 1\n");
    let tool_src = tmp.join("tool/src");
    write(&tool_src.join("acme/__init__.py"), "");
    write(&tool_src.join("acme/api.py"), "def ping(): pass\n");
    write(&tool_src.join("tool.py"), "def main(): pass\n");
    let excludes = vec![package.join("skip.py").to_string_lossy().to_string()];
    let files = discover(&[package.clone(), tool_src.clone()], &excludes);
    let got: Vec<(&Path, &str, &Path)> = files
        .iter()
        .map(|f| (f.path.as_path(), f.module_name.as_str(), f.root.as_path()))
        .collect();
    assert_eq!(
        got,
        [
            (
                package.join("__init__.py").as_path(),
                "mylib",
                package.as_path()
            ),
            (
                package.join("core.py").as_path(),
                "mylib.core",
                package.as_path()
            ),
            (
                tool_src.join("tool.py").as_path(),
                "tool",
                tool_src.as_path()
            ),
            (
                tool_src.join("acme/__init__.py").as_path(),
                "acme",
                tool_src.as_path()
            ),
            (
                tool_src.join("acme/api.py").as_path(),
                "acme.api",
                tool_src.as_path()
            ),
        ]
    );
    let core = parse_file(&files[1].path, &files[1].root, DocstringStyle::Numpy).unwrap();
    assert_eq!(core.name, "mylib.core");
    assert_eq!(core.functions[0].args[0].description, "Value.");
    assert_eq!(core.language, folio_ir::Language::Python);
    assert_eq!(core.source_file, files[1].path.display().to_string());
}

#[test]
fn configured_paths_excludes_and_numpy_style() {
    let (_guard, tmp) = tempdir();
    let source = tmp.join("src/demo");
    write(&source.join("__init__.py"), "\"\"\"Demo package.\"\"\"\n");
    write(
        &source.join("core.py"),
        "\"\"\"Core module.\"\"\"\n\ndef add(a, b):\n    \"\"\"Add values.\n\n    Parameters\n    ----------\n    a : int\n        First value.\n    b : int\n        Second value.\n    Returns\n    -------\n    int\n        Sum.\n    \"\"\"\n    return a + b\n",
    );
    let excluded = source.join("internal.py");
    write(&excluded, "\"\"\"Internal.\"\"\"\n");
    let missing = tmp.join("missing");
    let excludes = vec![excluded.to_string_lossy().to_string()];
    let files = discover(&[source.clone(), missing], &excludes);
    let got: Vec<&str> = files.iter().map(|f| f.module_name.as_str()).collect();
    assert_eq!(got, ["demo", "demo.core"]);
    let core = parse_file(&files[1].path, &files[1].root, DocstringStyle::Numpy).unwrap();
    let add = &core.functions[0];
    assert_eq!(add.args[0].description, "First value.");
    assert_eq!(add.returns.as_ref().unwrap().description, "Sum.");
}
