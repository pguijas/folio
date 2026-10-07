use super::*;
use crate::testing::MemoryBuilder;

#[test]
fn entry_lines_match_the_sidebar_serializer() {
    assert_eq!(
        entry_lines("http", &MetaValue::Title("HTTP \"API\" \\".into())),
        ["  \"http\": \"HTTP \\\"API\\\" \\\\\","]
    );
    assert_eq!(
        entry_lines("index", &MetaValue::HiddenIndex),
        ["  \"index\": {", "    \"display\": \"hidden\",", "  },"]
    );
    assert_eq!(slug_label("cookie_caper-api"), "Cookie Caper Api");
    assert_eq!(slug_label("v2 API"), "V2 Api");
}

#[test]
fn preserves_nested_and_escaped_entries() {
    let existing = "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"guides\": {\n    \"title\": \"Guides \\\"advanced\\\"\",\n    \"theme\": {\n      \"collapsed\": true,\n    },\n  },\n  \"faq\": \"Questions & \\\"Answers\\\"\",\n}";
    let mut builder = MemoryBuilder::with_meta([("api-reference", existing)]);
    merge_meta_entry(&mut builder, "api-reference", "http", "HTTP API", true).unwrap();
    let expected = format!(
        "{}  \"http\": \"HTTP API\",\n}}",
        &existing[..existing.rfind('}').unwrap()]
    );
    assert_eq!(builder.meta["api-reference"], expected);
}

#[test]
fn replaces_only_its_own_entry_and_keeps_the_trailing_newline() {
    let existing = "export default {\n  \"http\": {\n    \"title\": \"Old {HTTP} title\",\n    \"theme\": {\n      \"collapsed\": true,\n    },\n  },\n  \"guides\": {\n    \"title\": \"Guides\",\n    \"theme\": {\n      \"collapsed\": true,\n    },\n  },\n}\n";
    let mut builder = MemoryBuilder::with_meta([("api-reference", existing)]);
    merge_meta_entry(&mut builder, "api-reference", "http", "New API", false).unwrap();
    assert_eq!(
            builder.meta["api-reference"],
            "export default {\n  \"http\": \"New API\",\n  \"guides\": {\n    \"title\": \"Guides\",\n    \"theme\": {\n      \"collapsed\": true,\n    },\n  },\n}\n"
        );
}

#[test]
fn adds_the_hidden_index_only_when_missing() {
    let mut builder = MemoryBuilder::with_meta([(
        "api-reference",
        "export default {\n  \"petstore\": \"Petstore\",\n}\n",
    )]);
    merge_meta_entry(&mut builder, "api-reference", "http", "HTTP API", true).unwrap();
    assert_eq!(
            builder.meta["api-reference"],
            "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"petstore\": \"Petstore\",\n  \"http\": \"HTTP API\",\n}\n"
        );
    merge_meta_entry(&mut builder, "api-reference", "http", "HTTP API", true).unwrap();
    assert_eq!(
        builder.meta["api-reference"].matches("\"index\"").count(),
        1
    );
}

#[test]
fn writes_a_fresh_module_when_the_file_is_empty() {
    let mut builder = MemoryBuilder::default();
    merge_meta_entry(&mut builder, "api-reference", "http", "HTTP API", true).unwrap();
    assert_eq!(
            builder.meta["api-reference"],
            "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"http\": \"HTTP API\",\n}"
        );
    let mut builder = MemoryBuilder::with_meta([("", "   \n")]);
    merge_meta_entry(&mut builder, "", "api-reference", "API Reference", false).unwrap();
    assert_eq!(
        builder.meta[""],
        "export default {\n  \"api-reference\": \"API Reference\",\n}"
    );
}

#[test]
fn appends_when_the_structure_is_unrecognized() {
    let existing = "// hand-written meta\nexport default someHelper({})\n";
    let mut builder = MemoryBuilder::with_meta([("", existing)]);
    merge_meta_entry(&mut builder, "", "api-reference", "API Reference", false).unwrap();
    assert_eq!(
        builder.meta[""],
        format!(
            "{}\n  \"api-reference\": \"API Reference\",\n",
            existing.trim_end_matches('\n')
        )
    );
}

#[test]
fn write_route_meta_merges_the_root_and_the_page_entries() {
    let mut builder = MemoryBuilder::default();
    write_route_meta(&mut builder, "api-reference/http", "Cookie Caper API").unwrap();
    assert_eq!(
        builder.meta[""],
        "export default {\n  \"api-reference\": \"API Reference\",\n}"
    );
    assert_eq!(
            builder.meta["api-reference"],
            "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"http\": \"Cookie Caper API\",\n}"
        );
    let mut builder = MemoryBuilder::default();
    write_route_meta(&mut builder, "/guides/http_api/", "HTTP").unwrap();
    assert_eq!(
        builder.meta[""],
        "export default {\n  \"guides\": \"Guides\",\n}"
    );
    assert_eq!(
        builder.meta["guides"],
        "export default {\n  \"http_api\": \"HTTP\",\n}"
    );
    let mut builder = MemoryBuilder::default();
    write_route_meta(&mut builder, "openapi", "Top").unwrap();
    assert_eq!(
        builder.meta[""],
        "export default {\n  \"openapi\": \"Top\",\n}"
    );
    write_route_meta(&mut builder, "///", "Nothing").unwrap();
    assert_eq!(builder.meta.len(), 1);
}
