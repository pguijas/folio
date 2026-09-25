//! Rustdoc markup as plain Markdown. A doc comment is written for rustdoc:
//! its code blocks are Rust unless tagged otherwise and hide their `# ` setup
//! lines, and its intra-doc links name items by path. On a Folio page an
//! untagged block is tagged `rust`, the hidden lines are dropped (`##` reads
//! as `#`), and a link to a path keeps its text without the brackets.

use std::collections::HashMap;

/// The fence attributes rustdoc reads as "this block is Rust".
const RUST_ATTRIBUTES: [&str; 7] = [
    "rust",
    "ignore",
    "should_panic",
    "no_run",
    "compile_fail",
    "test_harness",
    "standalone_crate",
];

/// The `kind@` prefixes that disambiguate an intra-doc link.
const DISAMBIGUATORS: [&str; 19] = [
    "struct",
    "enum",
    "trait",
    "union",
    "fn",
    "mod",
    "type",
    "const",
    "static",
    "macro",
    "value",
    "prim",
    "primitive",
    "method",
    "field",
    "variant",
    "tymethod",
    "derive",
    "attr",
];

/// A doc comment as Markdown any page renders the way rustdoc would.
pub(crate) fn plain_markdown(text: &str) -> String {
    let definitions = definitions(text);
    let mut out: Vec<String> = Vec::new();
    // The open fence: its marker, its length and whether it holds Rust.
    let mut fence: Option<(char, usize, bool)> = None;
    for line in text.split('\n') {
        let indent = line.len() - line.trim_start_matches(' ').len();
        let body = &line[indent..];
        let marker = body.chars().next().filter(|c| *c == '`' || *c == '~');
        let run = marker.map_or(0, |c| body.chars().take_while(|x| *x == c).count());
        let is_fence = indent <= 3 && run >= 3;
        match fence {
            Some((open, len, _)) if is_fence && marker == Some(open) && run >= len => {
                if body[run..].trim().is_empty() {
                    fence = None;
                }
                out.push(line.to_string());
            }
            Some((_, _, true)) => {
                let code = line.trim_start();
                if code == "#" || code.starts_with("# ") {
                    continue;
                }
                match code.strip_prefix("##") {
                    Some(rest) => {
                        out.push(format!("{}#{rest}", &line[..line.len() - code.len()]));
                    }
                    None => out.push(line.to_string()),
                }
            }
            Some(_) => out.push(line.to_string()),
            None if is_fence => {
                let marker = marker.expect("a fence has a marker");
                let info = body[run..].trim();
                let rust = is_rust(info);
                fence = Some((marker, run, rust));
                out.push(match rust {
                    true => format!("{}{}rust", &line[..indent], &body[..run]),
                    false => line.to_string(),
                });
            }
            None => {
                if let Some((label, _)) = definition(line) {
                    if definitions.get(&label) == Some(&true) {
                        continue;
                    }
                }
                out.push(links(line, &definitions));
            }
        }
    }
    // A dropped definition block leaves no blank tail behind.
    while out.len() > 1 && out.iter().rev().take(2).all(|line| line.trim().is_empty()) {
        out.pop();
    }
    out.join("\n")
}

/// Whether a fence's info string makes its block Rust for rustdoc.
fn is_rust(info: &str) -> bool {
    info.split(|c: char| c == ',' || c.is_whitespace())
        .filter(|token| !token.is_empty())
        .all(|token| {
            RUST_ATTRIBUTES.contains(&token)
                || token.starts_with("edition")
                || (token.len() > 1
                    && token.starts_with('E')
                    && token[1..].chars().all(|c| c.is_ascii_digit()))
        })
}

/// Every `[label]: target` reference definition outside a fence, by
/// lowercased label: `true` when the target is an item path.
fn definitions(text: &str) -> HashMap<String, bool> {
    let mut found = HashMap::new();
    let mut fenced = false;
    for line in text.split('\n') {
        let body = line.trim_start();
        if body.starts_with("```") || body.starts_with("~~~") {
            fenced = !fenced;
            continue;
        }
        if fenced {
            continue;
        }
        if let Some((label, target)) = definition(line) {
            found.insert(label, is_path(&target));
        }
    }
    found
}

/// A `[label]: target` line: the lowercased label and the target.
fn definition(line: &str) -> Option<(String, String)> {
    let body = line.trim_start();
    let rest = body.strip_prefix('[')?;
    let (label, after) = rest.split_once("]:")?;
    let target = after.split_whitespace().next()?;
    (!label.is_empty() && !label.contains(']')).then(|| (label.to_lowercase(), target.to_string()))
}

/// Whether a link target names an item rather than a URL: `Foo`,
/// `crate::a::Foo`, `Self::bar()`, `fn@baz`, `vec!`.
fn is_path(target: &str) -> bool {
    let target = target.trim_matches('`');
    let target = match target.split_once('@') {
        Some((kind, rest)) if DISAMBIGUATORS.contains(&kind) => rest,
        _ => target,
    };
    let target = target
        .strip_suffix("()")
        .or_else(|| target.strip_suffix('!'))
        .unwrap_or(target);
    !target.is_empty()
        && target.split("::").all(|segment| {
            let segment = segment.split('<').next().unwrap_or_default();
            segment
                .chars()
                .next()
                .is_some_and(|c| c.is_alphabetic() || c == '_')
                && segment.chars().all(|c| c.is_alphanumeric() || c == '_')
        })
}

/// Whether bare `[text]` reads as an item link rather than prose in
/// brackets: code, a path, a type-like capital, a call or a macro.
fn looks_like_item(text: &str) -> bool {
    is_path(text)
        && (text.starts_with('`')
            || text.contains('@')
            || text.contains("::")
            || text.starts_with(char::is_uppercase)
            || text.ends_with("()")
            || text.ends_with('!'))
}

/// One line with its intra-doc links reduced to their text; code spans and
/// URL links are left as written.
fn links(line: &str, definitions: &HashMap<String, bool>) -> String {
    let chars: Vec<char> = line.chars().collect();
    let mut out = String::new();
    let mut i = 0;
    while i < chars.len() {
        match chars[i] {
            '`' => {
                let run = chars[i..].iter().take_while(|c| **c == '`').count();
                let close = (i + run..chars.len()).find(|&j| {
                    chars[j..].iter().take_while(|c| **c == '`').count() == run
                        && (j == 0 || chars[j - 1] != '`')
                });
                let end = close.map_or(i + run, |j| j + run);
                out.extend(&chars[i..end]);
                i = end;
            }
            '[' => {
                let Some((text, end)) = bracketed(&chars, i) else {
                    out.push('[');
                    i += 1;
                    continue;
                };
                let before = i.checked_sub(1).map(|j| chars[j]);
                match chars.get(end) {
                    Some('(') => match closing(&chars, end, '(', ')') {
                        Some(stop) => {
                            let target: String = chars[end + 1..stop].iter().collect();
                            if is_path(&target) {
                                out.push_str(&text);
                            } else {
                                out.extend(&chars[i..=stop]);
                            }
                            i = stop + 1;
                        }
                        None => {
                            out.extend(&chars[i..end]);
                            i = end;
                        }
                    },
                    Some('[') => match bracketed(&chars, end) {
                        Some((label, stop)) => {
                            let collapsed = label.is_empty();
                            let label = if collapsed { text.clone() } else { label };
                            let strip = match definitions.get(&label.to_lowercase()) {
                                Some(path) => *path,
                                None => is_path(&label),
                            };
                            if strip && collapsed {
                                out.push_str(&shown(&text));
                            } else if strip {
                                out.push_str(&text);
                            } else {
                                out.extend(&chars[i..stop]);
                            }
                            i = stop;
                        }
                        None => {
                            out.extend(&chars[i..end]);
                            i = end;
                        }
                    },
                    _ => {
                        let prose =
                            before.is_some_and(|c| c.is_alphanumeric() || "_])!".contains(c));
                        let strip = match definitions.get(&text.to_lowercase()) {
                            Some(path) => *path,
                            None => !prose && looks_like_item(&text),
                        };
                        if strip {
                            out.push_str(&shown(&text));
                        } else {
                            out.extend(&chars[i..end]);
                        }
                        i = end;
                    }
                }
            }
            c => {
                out.push(c);
                i += 1;
            }
        }
    }
    out
}

/// A link that is its own target shows without its `kind@` disambiguator,
/// as rustdoc shows it.
fn shown(text: &str) -> String {
    let code = text.len() > 1 && text.starts_with('`') && text.ends_with('`');
    let inner = if code { &text[1..text.len() - 1] } else { text };
    let bare = match inner.split_once('@') {
        Some((kind, rest)) if DISAMBIGUATORS.contains(&kind) => rest,
        _ => inner,
    };
    if code {
        format!("`{bare}`")
    } else {
        bare.to_string()
    }
}

/// The text of the `[…]` opening at `open` and the index just past its `]`.
fn bracketed(chars: &[char], open: usize) -> Option<(String, usize)> {
    let stop = closing(chars, open, '[', ']')?;
    Some((chars[open + 1..stop].iter().collect(), stop + 1))
}

/// The index of the delimiter closing the one at `open`, backtick spans skipped.
fn closing(chars: &[char], open: usize, left: char, right: char) -> Option<usize> {
    let mut depth = 0;
    let mut code = false;
    for (j, c) in chars.iter().enumerate().skip(open) {
        match *c {
            '`' => code = !code,
            _ if code => {}
            c if c == left => depth += 1,
            c if c == right => {
                depth -= 1;
                if depth == 0 {
                    return Some(j);
                }
            }
            _ => {}
        }
    }
    None
}

#[cfg(test)]
#[path = "rustdoc_tests.rs"]
mod tests;
