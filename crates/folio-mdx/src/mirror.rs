//! MDX to lossy Markdown, the per-page mirror agents read: prose, code,
//! headings and tables survive; JSX shells go, a few components leave a text
//! trace, and the API reference's class cards and parameter tables become
//! Markdown.

use serde_json::Value;

use crate::re;

/// Converts final MDX into the agent-readable Markdown mirror. Ends in exactly
/// one `\n`; empty input is `"\n"`. Outside code, the MDX escapes are undone
/// and a heading loses its `[#id]`: the mirror reads as the page does.
pub fn mdx_to_markdown(content: &str) -> String {
    let mut markdown = restore_mermaid(strip_leading_frontmatter(content));
    let mut protected = Vec::new();
    markdown = protect_fenced_blocks(&markdown, &mut protected);
    markdown = protect_inline_code(&markdown, &mut protected);
    markdown = re(r"(?m)^(?:import|export)\s+.+$")
        .replace_all(&markdown, "")
        .into_owned();
    // An empty anchor element (the API reference's class ids) says nothing.
    markdown = re(r#"(?m)^<span id="[^"\n]*" />[ \t]*$"#)
        .replace_all(&markdown, "")
        .into_owned();
    markdown = strip_component_tags(&markdown, &mut protected);
    markdown = re(r"(?m)^(#{1,6}[ \t].*?)[ \t]*(?:\[#[^\]\n]*\])?[ \t]*$")
        .replace_all(&markdown, "$1")
        .into_owned();
    markdown = unescape_mdx_text(&markdown);
    for (index, code) in protected.iter().enumerate() {
        markdown = markdown.replace(&placeholder(index), code);
    }
    markdown = re(r"(?m)^[ \t]+$").replace_all(&markdown, "").into_owned();
    markdown = re(r"\n{3,}").replace_all(&markdown, "\n\n").into_owned();
    format!("{}\n", markdown.trim())
}

fn placeholder(index: usize) -> String {
    format!("\u{0}FOLIO_MARKDOWN_CODE_{index}\u{0}")
}

/// `text` with every placeholder put back: a JSX prop is read as written.
fn restore(text: &str, protected: &[String]) -> String {
    let mut text = text.to_string();
    for (index, code) in protected.iter().enumerate().rev() {
        text = text.replace(&placeholder(index), code);
    }
    text
}

/// The inverse of `escape_mdx_text`: `\{`, `\}`, `&lt;` and `&gt;` read as
/// the characters they stand for.
fn unescape_mdx_text(text: &str) -> String {
    text.replace("\\{", "{")
        .replace("\\}", "}")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
}

/// `\A---\n.*?\n---\n?`
fn strip_leading_frontmatter(content: &str) -> &str {
    let Some(rest) = content.strip_prefix("---\n") else {
        return content;
    };
    let Some(end) = rest.find("\n---") else {
        return content;
    };
    let after = &rest[end + 4..];
    after.strip_prefix('\n').unwrap_or(after)
}

/// `<Mermaid chart={`…`} />` back to a ```` ```mermaid ```` fence, undoing the
/// `` \` `` and `\${` escapes (a doubled backslash stays doubled, as before).
fn restore_mermaid(content: &str) -> String {
    let mut out = String::with_capacity(content.len());
    let mut pos = 0;
    while let Some(found) = content[pos..].find("<Mermaid") {
        let start = pos + found;
        match mermaid_chart(&content[start..]) {
            Some((chart, len)) => {
                out.push_str(&content[pos..start]);
                let chart = chart.replace("\\`", "`").replace("\\${", "${");
                out.push_str(&format!("```mermaid\n{chart}\n```"));
                pos = start + len;
            }
            None => {
                out.push_str(&content[pos..start + 1]);
                pos = start + 1;
            }
        }
    }
    out.push_str(&content[pos..]);
    out
}

/// Parses `<Mermaid\s+chart=\{`(chart)`\}\s*/>` at the start of `text`;
/// returns the chart and the matched length.
fn mermaid_chart(text: &str) -> Option<(&str, usize)> {
    let after_name = text.strip_prefix("<Mermaid")?;
    let attrs = after_name.trim_start();
    if attrs.len() == after_name.len() {
        return None;
    }
    let chart_start = text.len() - attrs.strip_prefix("chart={`")?.len();
    let bytes = text.as_bytes();
    let mut i = chart_start;
    // ponytail: greedy `(?:\\.|[^`])*` without backtracking; a malformed tail
    // leaves the text alone instead of retrying shorter charts.
    loop {
        match bytes.get(i) {
            None => return None,
            Some(b'`') => break,
            Some(b'\\') => i += 1 + text[i + 1..].chars().next()?.len_utf8(),
            Some(_) => i += text[i..].chars().next()?.len_utf8(),
        }
    }
    let tail = text[i + 1..].strip_prefix('}')?.trim_start();
    tail.strip_prefix("/>")?;
    Some((&text[chart_start..i], text.len() - tail.len() + 2))
}

/// Leading `[ \t>]*` of a line, then the fence run: (char, length).
fn fence_run(line: &str) -> Option<(u8, usize)> {
    let rest = line.trim_start_matches([' ', '\t', '>']);
    let first = *rest.as_bytes().first()?;
    if first != b'`' && first != b'~' {
        return None;
    }
    let run = rest.bytes().take_while(|&b| b == first).count();
    (run >= 3).then_some((first, run))
}

/// Swaps every fenced block for a placeholder, emulating
/// `(?ms)^[ \t>]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t>]*\1[ \t]*$`: the opener may be
/// indented or blockquoted, the closer is the same run exactly.
fn protect_fenced_blocks(text: &str, protected: &mut Vec<String>) -> String {
    let lines: Vec<&str> = text.split('\n').collect();
    let closes = |line: &str, ch: u8, len: usize| {
        let rest = line.trim_start_matches([' ', '\t', '>']);
        rest.bytes().take_while(|&b| b == ch).count() == len
            && rest[len..].trim_matches([' ', '\t']).is_empty()
    };
    let mut out: Vec<String> = Vec::with_capacity(lines.len());
    let mut i = 0;
    while i < lines.len() {
        let Some((ch, run)) = fence_run(lines[i]).filter(|_| i + 1 < lines.len()) else {
            out.push(lines[i].to_string());
            i += 1;
            continue;
        };
        let closer = (3..=run)
            .rev()
            .find_map(|len| (i + 1..lines.len()).find(|&j| closes(lines[j], ch, len)));
        match closer {
            Some(j) => {
                out.push(placeholder(protected.len()));
                protected.push(lines[i..=j].join("\n"));
                i = j + 1;
            }
            None => {
                out.push(lines[i].to_string());
                i += 1;
            }
        }
    }
    out.join("\n")
}

/// End of the span at `start` for `(?<!`)(`+)([^\n]*?)\1(?!`)`: the body may
/// be empty and may not cross a line; the closer is not followed by a tick.
fn inline_code_no_newline(text: &str, start: usize) -> Option<usize> {
    let b = text.as_bytes();
    let run = b[start..].iter().take_while(|&&c| c == b'`').count();
    for n in (1..=run).rev() {
        let mut e = start + n;
        while e + n <= b.len() {
            if b[e..e + n].iter().all(|&c| c == b'`') && b.get(e + n) != Some(&b'`') {
                return Some(e + n);
            }
            if b[e] == b'\n' {
                break;
            }
            e += 1;
        }
    }
    None
}

fn protect_inline_code(text: &str, protected: &mut Vec<String>) -> String {
    let b = text.as_bytes();
    let mut out = String::with_capacity(text.len());
    let (mut pos, mut i) = (0, 0);
    while i < b.len() {
        if b[i] == b'`' && (i == 0 || b[i - 1] != b'`') {
            if let Some(end) = inline_code_no_newline(text, i) {
                out.push_str(&text[pos..i]);
                out.push_str(&placeholder(protected.len()));
                protected.push(text[i..end].to_string());
                pos = end;
                i = end;
                continue;
            }
        }
        i += 1;
    }
    out.push_str(&text[pos..]);
    out
}

/// `<\s*(/?)\s*([A-Z][A-Za-z0-9]*)` at the start of `text`: (closing, name, len).
fn tag_open(text: &str) -> Option<(bool, &str, usize)> {
    let mut rest = text.strip_prefix('<')?.trim_start();
    let closing = rest.starts_with('/');
    if closing {
        rest = rest[1..].trim_start();
    }
    let name_len = rest
        .bytes()
        .take_while(|b| b.is_ascii_alphanumeric())
        .count();
    if !rest.as_bytes().first()?.is_ascii_uppercase() {
        return None;
    }
    Some((
        closing,
        &rest[..name_len],
        text.len() - rest.len() + name_len,
    ))
}

/// Index of the `>` that ends the tag whose attributes start at `cursor`:
/// the first `>` at brace depth 0 outside a `"`, `'` or `` ` `` string.
fn tag_end(content: &str, mut cursor: usize) -> Option<usize> {
    let b = content.as_bytes();
    let (mut quote, mut escaped, mut depth) = (0u8, false, 0usize);
    while cursor < b.len() {
        let c = b[cursor];
        if quote != 0 {
            if escaped {
                escaped = false;
            } else if c == b'\\' {
                escaped = true;
            } else if c == quote {
                quote = 0;
            }
        } else {
            match c {
                b'"' | b'\'' | b'`' => quote = c,
                b'{' => depth += 1,
                b'}' if depth > 0 => depth -= 1,
                b'>' if depth == 0 => return Some(cursor),
                _ => {}
            }
        }
        cursor += 1;
    }
    None
}

/// Removes PascalCase JSX tags, keeping their children and a text trace for a
/// few components; lowercase HTML and stray `<` are copied through. What an
/// API component becomes is final Markdown, kept out of the unescaping.
fn strip_component_tags(content: &str, protected: &mut Vec<String>) -> String {
    let mut out = String::with_capacity(content.len());
    let mut cursor = 0;
    while cursor < content.len() {
        let Some(found) = content[cursor..].find('<') else {
            break;
        };
        let start = cursor + found;
        let Some((closing, name, open_len)) = tag_open(&content[start..]) else {
            out.push_str(&content[cursor..start + 1]);
            cursor = start + 1;
            continue;
        };
        let Some(end) = tag_end(content, start + open_len) else {
            out.push_str(&content[cursor..]);
            return out;
        };
        out.push_str(&content[cursor..start]);
        let tag = &content[start..=end];
        match api_markdown(&restore(tag, protected), name, closing) {
            Some(markdown) => {
                out.push_str(&format!("\n{}\n", placeholder(protected.len())));
                protected.push(markdown);
            }
            None => out.push_str(&tag_markdown(tag, name, closing)),
        }
        cursor = end + 1;
    }
    out.push_str(&content[cursor..]);
    out
}

/// The value of the string prop `name` (`\bname\s*=\s*(["'])(.*?)\1`), with
/// escaped quotes unescaped; JSX expression props are never read.
fn string_prop(tag: &str, name: &str) -> String {
    let mut from = 0;
    while let Some(found) = tag[from..].find(name) {
        let at = from + found;
        from = at + 1;
        let word_before = tag[..at]
            .chars()
            .next_back()
            .is_some_and(|c| c.is_alphanumeric() || c == '_');
        if word_before {
            continue;
        }
        let rest = tag[at + name.len()..].trim_start();
        let Some(rest) = rest.strip_prefix('=') else {
            continue;
        };
        let rest = rest.trim_start();
        let Some(quote) = rest.chars().next().filter(|&q| q == '"' || q == '\'') else {
            continue;
        };
        let value = &rest[1..];
        if let Some(end) = value.find(quote) {
            return value[..end].replace(&format!("\\{quote}"), &quote.to_string());
        }
    }
    String::new()
}

/// The value of the expression prop `name` (`name={...}`) read as JSON; a
/// prop that is not JSON (a hand-written JS literal) reads as absent.
fn json_prop(tag: &str, name: &str) -> Option<Value> {
    let mut from = 0;
    while let Some(found) = tag[from..].find(name) {
        let at = from + found;
        from = at + 1;
        let word_before = tag[..at]
            .chars()
            .next_back()
            .is_some_and(|c| c.is_alphanumeric() || c == '_');
        let rest = tag[at + name.len()..].trim_start();
        let Some(rest) = rest.strip_prefix('=').map(str::trim_start) else {
            continue;
        };
        if word_before || !rest.starts_with('{') {
            continue;
        }
        let offset = tag.len() - rest.len();
        let close = expression_end(tag, offset)?;
        return serde_json::from_str(&tag[offset + 1..close]).ok();
    }
    None
}

/// Index of the `}` closing the `{` at `open`, outside JSON strings.
fn expression_end(text: &str, open: usize) -> Option<usize> {
    let (mut depth, mut in_string, mut escaped) = (0usize, false, false);
    for (i, c) in text[open..].char_indices() {
        if in_string {
            match (escaped, c) {
                (true, _) => escaped = false,
                (false, '\\') => escaped = true,
                (false, '"') => in_string = false,
                _ => {}
            }
            continue;
        }
        match c {
            '"' => in_string = true,
            '{' => depth += 1,
            '}' => {
                depth -= 1;
                if depth == 0 {
                    return Some(open + i);
                }
            }
            _ => {}
        }
    }
    None
}

fn json_text<'a>(value: &'a Value, key: &str) -> &'a str {
    value.get(key).and_then(Value::as_str).unwrap_or("")
}

/// A GFM table cell: one line, pipes escaped.
fn table_cell(text: &str) -> String {
    text.split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .replace('|', "\\|")
}

/// An inline code span that survives a backtick in its text.
fn code_span(text: &str) -> String {
    if text.contains('`') {
        format!("`` {text} ``")
    } else {
        format!("`{text}`")
    }
}

/// What the API reference's generated components say, as Markdown: the class
/// card, the parameter table and the module index. `None` for any other tag.
fn api_markdown(tag: &str, name: &str, closing: bool) -> Option<String> {
    if closing {
        return None;
    }
    match name {
        "ClassOverview" => {
            let class = string_prop(tag, "name");
            if class.is_empty() {
                return None;
            }
            let mut lines: Vec<String> = json_prop(tag, "decorators")
                .as_ref()
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .map(|d| format!("{}\n", code_span(&format!("@{d}"))))
                .collect();
            let bases: Vec<String> = json_prop(tag, "bases")
                .as_ref()
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .map(|base| match base {
                    Value::String(name) => name.clone(),
                    entry => match json_text(entry, "href") {
                        "" => json_text(entry, "name").to_string(),
                        href => format!("[{}]({href})", json_text(entry, "name")),
                    },
                })
                .collect();
            let bases = if bases.is_empty() {
                String::new()
            } else {
                format!("({})", bases.join(", "))
            };
            lines.push(format!("**class {class}{bases}**"));
            Some(lines.join("\n"))
        }
        "ParamTable" => {
            let args = json_prop(tag, "args")?;
            let args = args.as_array()?;
            if args.is_empty() {
                return Some(String::new());
            }
            let mut rows = vec![
                "| Parameter | Type | Default | Description |".to_string(),
                "| --- | --- | --- | --- |".to_string(),
            ];
            rows.extend(args.iter().map(|arg| {
                let ty = code_span(&table_cell(json_text(arg, "type")));
                let ty = match json_text(arg, "href") {
                    "" => ty,
                    href => format!("[{ty}]({href})"),
                };
                let default = match json_text(arg, "default") {
                    "" => String::new(),
                    value => code_span(&table_cell(value)),
                };
                format!(
                    "| {} | {ty} | {default} | {} |",
                    code_span(&table_cell(json_text(arg, "name"))),
                    table_cell(json_text(arg, "description"))
                )
            }));
            Some(rows.join("\n"))
        }
        "ApiReferenceIndex" => {
            let modules = json_prop(tag, "modules")?;
            let items: Vec<String> = modules
                .as_array()?
                .iter()
                .map(|module| match json_text(module, "description") {
                    "" => format!("- **{}**", json_text(module, "name")),
                    text => format!("- **{}**: {text}", json_text(module, "name")),
                })
                .collect();
            Some(items.join("\n"))
        }
        _ => None,
    }
}

fn tag_markdown(tag: &str, name: &str, closing: bool) -> String {
    if closing {
        return String::new();
    }
    let self_closing = tag[..tag.len() - 1].trim_end().ends_with('/');
    if self_closing && matches!(name, "FeatureCard" | "CommandCard") {
        let mut title = string_prop(tag, "title");
        if title.is_empty() {
            title = string_prop(tag, "command");
        }
        let description = string_prop(tag, "description");
        let href = string_prop(tag, "href");
        if title.is_empty() && description.is_empty() {
            return String::new();
        }
        let label = if !title.is_empty() && !href.is_empty() {
            format!("[{title}]({href})")
        } else {
            title
        };
        return match (label.is_empty(), description.is_empty()) {
            (false, false) => format!("\n- **{label}**: {description}\n"),
            (false, true) => format!("\n- **{label}**\n"),
            (true, _) => format!("\n- {description}\n"),
        };
    }
    if !self_closing {
        let label_prop = match name {
            "AccordionItem" | "Step" => Some("title"),
            "TabItem" => Some("label"),
            _ => None,
        };
        if let Some(prop) = label_prop {
            let label = string_prop(tag, prop);
            if !label.is_empty() {
                return format!("\n### {label}\n\n");
            }
        }
        if matches!(name, "Callout" | "PullQuote" | "PreviewCode") {
            let mut label = string_prop(tag, "title");
            if label.is_empty() {
                label = string_prop(tag, "kicker");
            }
            if !label.is_empty() {
                return format!("\n**{label}**\n\n");
            }
        }
    }
    String::new()
}

#[cfg(test)]
#[path = "mirror_tests.rs"]
mod tests;
