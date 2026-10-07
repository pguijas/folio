//! `inspect.cleandoc` (CPython 3.12): the docstring normalisation `ast.get_docstring`
//! and every style parser apply.

/// Expand tabs to stops of 8, strip the common margin of lines after the first,
/// drop leading and trailing empty lines.
pub fn cleandoc(text: &str) -> String {
    if text.is_empty() {
        return String::new();
    }
    let expanded = expand_tabs(text);
    let lines: Vec<&str> = expanded.split('\n').collect();

    // Margin in characters over the non-blank lines after the first; CPython
    // slices by code point, so a byte margin would split U+00A0 indentation.
    let margin = lines[1..]
        .iter()
        .filter(|line| !line.trim_start().is_empty())
        .map(|line| line.chars().count() - line.trim_start().chars().count())
        .min()
        .unwrap_or(0);

    let mut out: Vec<String> = Vec::with_capacity(lines.len());
    out.push(lines[0].trim_start().to_string());
    // Sliced unconditionally, like `lines[i] = lines[i][margin:]`.
    out.extend(lines[1..].iter().map(|l| l.chars().skip(margin).collect()));

    // Only truly empty strings are falsy in Python; whitespace-only lines stay.
    while out.last().is_some_and(String::is_empty) {
        out.pop();
    }
    let first_kept = out.iter().position(|l| !l.is_empty()).unwrap_or(out.len());
    out[first_kept..].join("\n")
}

/// `str.expandtabs()` with tab stops of 8; the column resets at `\n` and `\r`.
fn expand_tabs(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut col = 0usize;
    for ch in text.chars() {
        match ch {
            '\t' => {
                let spaces = 8 - (col % 8);
                out.extend(std::iter::repeat_n(' ', spaces));
                col += spaces;
            }
            '\n' | '\r' => {
                out.push(ch);
                col = 0;
            }
            _ => {
                out.push(ch);
                col += 1;
            }
        }
    }
    out
}

#[cfg(test)]
#[path = "cleandoc_tests.rs"]
mod tests;
