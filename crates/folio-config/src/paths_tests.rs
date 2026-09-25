use super::join_lexical;
use std::path::{Path, PathBuf};

#[test]
fn join_lexical_reproduces_pathlib_join() {
    for (base, p, expected) in [
        ("/x", "src/", "/x/src"),
        ("/x", "./src", "/x/src"),
        ("/x", "a//b/./c", "/x/a/b/c"),
        ("/x", "../y", "/x/../y"),
        ("/x", "/abs/p", "/abs/p"),
        ("/x", ".", "/x"),
        ("/x", "", "/x"),
        ("rel", "src", "rel/src"),
        ("", "src", "src"),
    ] {
        assert_eq!(
            join_lexical(Path::new(base), p),
            PathBuf::from(expected),
            "join_lexical({base:?}, {p:?})"
        );
    }
}
