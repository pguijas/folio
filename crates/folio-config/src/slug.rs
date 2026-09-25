//! The shared slug rule, and the label rule that reads a slug back.

/// Lower-case, `.` to `-`, drop anything that is not a word char, whitespace
/// or `-`, then collapse whitespace/`_` runs and `-` runs to one `-`.
///
/// Unicode-aware, and the rule for every content slug. The preview-path slug
/// in `folio-cli`'s `github_pages` is the one deliberate exception: it names a
/// directory in the published Pages tree and stays ASCII.
pub fn slugify(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut pending_dash = false;
    for c in text.to_lowercase().trim().chars() {
        let dash = c == '.' || c == '-' || c == '_' || c.is_whitespace();
        if dash {
            pending_dash = true;
        } else if c.is_alphanumeric() {
            if pending_dash && !out.is_empty() {
                out.push('-');
            }
            pending_dash = false;
            out.push(c);
        }
    }
    out
}

/// Every run of letters starts upper and continues lower, anything else
/// passes through: `objective-c` reads `Objective-C`. For an id whose `-` and
/// `_` are word breaks rather than punctuation, use `slug_label`.
pub fn title_case(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut in_word = false;
    for c in text.chars() {
        if c.is_alphabetic() {
            if in_word {
                out.extend(c.to_lowercase());
            } else {
                out.extend(c.to_uppercase());
            }
            in_word = true;
        } else {
            out.push(c);
            in_word = false;
        }
    }
    out
}

/// A slug read back as a label: `_` and `-` are word breaks. `ocean-blue`
/// reads `Ocean Blue`.
pub fn slug_label(slug: &str) -> String {
    title_case(&slug.replace(['_', '-'], " "))
}

#[cfg(test)]
#[path = "slug_tests.rs"]
mod tests;
