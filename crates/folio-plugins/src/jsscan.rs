//! Comment- and import-aware scanning of `mdx-components.tsx` text, shared by
//! the contract validator, the drift guard and folio-site's injector.

use std::sync::LazyLock;

use regex::Regex;

/// A whole import statement: `import ... from "module"` (multi-line named
/// lists included) or a bare `import "module"`. Run on comment-stripped code.
static IMPORT_STATEMENT_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r#"(?m)^[ \t]*import\b[^'"]*?(?:'[^'\n]*'|"[^"\n]*")"#).expect("static pattern")
});

/// Drop `//...` and `/* ... */` comments, leaving `'`, `"` and backtick
/// literals intact (backslash escapes honoured).
pub fn strip_js_comments(code: &str) -> String {
    let bytes = code.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        let ch = bytes[i];
        let next = bytes.get(i + 1).copied();
        if ch == b'/' && next == Some(b'/') {
            i = code[i..].find('\n').map_or(bytes.len(), |end| i + end);
        } else if ch == b'/' && next == Some(b'*') {
            i = code[i + 2..]
                .find("*/")
                .map_or(bytes.len(), |end| i + 2 + end + 2);
        } else if matches!(ch, b'\'' | b'"' | b'`') {
            out.push(ch);
            i += 1;
            while i < bytes.len() {
                let current = bytes[i];
                out.push(current);
                if current == b'\\' && i + 1 < bytes.len() {
                    out.push(bytes[i + 1]);
                    i += 2;
                    continue;
                }
                i += 1;
                if current == ch {
                    break;
                }
            }
        } else {
            out.push(ch);
            i += 1;
        }
    }
    String::from_utf8(out).expect("comment stripping keeps char boundaries")
}

/// Every import statement in comment-stripped `code`, in order.
pub fn import_statements(code: &str) -> Vec<String> {
    IMPORT_STATEMENT_RE
        .find_iter(code)
        .map(|m| m.as_str().to_string())
        .collect()
}

/// `code` with every import statement removed.
pub fn strip_import_statements(code: &str) -> String {
    IMPORT_STATEMENT_RE.replace_all(code, "").into_owned()
}

/// Whether `name` is wired as a components-mapping entry (`Name,` / `Name:` /
/// `Name }` at any indentation) or an `as Name` re-export. `code` must be
/// comment- and import-stripped so a merely imported symbol never counts.
pub fn has_component_entry(code: &str, name: &str) -> bool {
    let n = regex::escape(name);
    Regex::new(&format!(r"\bas\s+{n}\b|\b{n}\s*[:,}}]"))
        .expect("escaped name")
        .is_match(code)
}

#[cfg(test)]
#[path = "jsscan_tests.rs"]
mod tests;
