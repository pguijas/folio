use super::*;

#[test]
fn strip_js_comments_preserves_strings_and_drops_comments() {
    let code = "const url = \"https://example.com\" // trailing comment\n/* block\ncomment */const other = 'a//b'\nconst t = `x // y \\` z`\n";
    let stripped = strip_js_comments(code);
    assert!(stripped.contains("\"https://example.com\""));
    assert!(stripped.contains("'a//b'"));
    assert!(stripped.contains("`x // y \\` z`"));
    assert!(!stripped.contains("trailing comment"));
    assert!(!stripped.contains("block"));
    // Unterminated comments run to the end of the text.
    assert_eq!(strip_js_comments("a /* never"), "a ");
    assert_eq!(strip_js_comments("a // never"), "a ");
}

#[test]
fn import_statements_match_whole_statements_including_multiline_lists() {
    let code = "import {\n  A,\n  B,\n} from \"./x\"\nimport y from 'y'\nimport \"side-effect\"\nconst Z = 1\n  import { C } from \"c\"; other\n";
    assert_eq!(
        import_statements(code),
        [
            "import {\n  A,\n  B,\n} from \"./x\"",
            "import y from 'y'",
            "import \"side-effect\"",
            "  import { C } from \"c\"",
        ]
    );
    let rest = strip_import_statements(code);
    assert!(!rest.contains("A,"));
    assert!(rest.contains("const Z = 1"));
    assert!(rest.contains("; other"));
}

#[test]
fn has_component_entry_accepts_entry_forms_only() {
    assert!(has_component_entry("  ParamTable,\n", "ParamTable"));
    assert!(has_component_entry("{ ParamTable: X }", "ParamTable"));
    assert!(has_component_entry("{ Foo, ParamTable }", "ParamTable"));
    assert!(has_component_entry(
        "export { Foo as ParamTable } from './foo'",
        "ParamTable"
    ));
    assert!(!has_component_entry("const ParamTable = 1", "ParamTable"));
    assert!(!has_component_entry("  MyParamTable,", "ParamTable"));
    assert!(!has_component_entry("  ParamTables,", "ParamTable"));
    assert!(has_component_entry("\"aria-label\": 1, Tabs,", "Tabs"));
}
