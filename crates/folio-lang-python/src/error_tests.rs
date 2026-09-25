use super::*;

#[test]
fn display_names_the_full_path_and_line() {
    let err = PythonSyntaxError {
        path: PathBuf::from("/p/broken.py"),
        message: "invalid syntax".to_string(),
        line: 1,
        column: 7,
        kind: ErrorKind::Syntax,
    };
    assert_eq!(err.to_string(), "invalid syntax (/p/broken.py, line 1)");
    let decode = ParseError::Decode {
        path: PathBuf::from("/p/latin1.py"),
        start: 6,
        end: 7,
    };
    assert_eq!(
        decode.to_string(),
        "'utf-8' codec can't decode bytes 6..7 in /p/latin1.py"
    );
}
