use super::*;

/// A crate with one published module, three unpublished ones and one declared
/// by nobody.
fn crate_at(dir: &Path) {
    let write = |rel: &str, text: &str| {
        let path = dir.join(rel);
        std::fs::create_dir_all(path.parent().expect("a parent")).unwrap();
        std::fs::write(path, text).unwrap();
    };
    write("Cargo.toml", "[package]\nname = \"my-crate\"\n");
    write(
        "src/lib.rs",
        "pub mod models;\nmod hidden;\npub(crate) mod internal;\n#[doc(hidden)]\npub mod unlisted;\n",
    );
    write("src/models.rs", "//! Models.\n");
    write("src/hidden.rs", "//! Hidden.\n");
    write("src/internal.rs", "//! Crate-visible only.\n");
    write("src/unlisted.rs", "//! Public but hidden from docs.\n");
    write("src/orphan.rs", "//! Declared by nobody.\n");
}

fn names(root: &Path) -> Vec<String> {
    discover(&[root.to_path_buf()], &[])
        .into_iter()
        .map(|file| file.module_name)
        .collect()
}

#[test]
fn a_root_publishes_the_crates_under_it_and_the_crate_it_sits_in() {
    let dir = tempfile::tempdir().unwrap();
    let workspace = dir.path().canonicalize().unwrap();
    crate_at(&workspace.join("crates/core"));

    assert_eq!(names(&workspace), ["my_crate", "my_crate::models"]);
    assert_eq!(
        names(&workspace.join("crates/core/src")),
        ["my_crate", "my_crate::models"]
    );
    assert!(names(&workspace.join("crates/core/src/orphan.rs")).is_empty());
}

#[test]
fn an_excluded_module_takes_its_children_with_it() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    crate_at(&root);
    let excluded = root.join("src/models.rs").to_string_lossy().to_string();

    let found = discover(std::slice::from_ref(&root), &[excluded]);
    let names: Vec<&str> = found.iter().map(|f| f.module_name.as_str()).collect();
    assert_eq!(names, ["my_crate"]);
}
