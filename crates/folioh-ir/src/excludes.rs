//! `source.<language>.exclude` matching with `fnmatch` semantics, `Path.resolve(strict=False)`
//! and Python `sorted(Path)` order: the rule every language reader discovers under.

use std::path::{Component, Path, PathBuf};

/// Whether the file matches any exclude entry: a glob (`*`, `?`, `[`) against the
/// resolved POSIX path, or a literal file/directory (component boundary).
pub fn is_excluded(path: &Path, excludes: &[String]) -> bool {
    let candidate = resolve_nonstrict(&path.to_string_lossy());
    for raw_exclude in excludes {
        let exclude_text = raw_exclude.replace('\\', "/");
        let exclude_text = exclude_text.trim_end_matches('/');
        if exclude_text.contains(['*', '?', '[']) {
            if fnmatch(&candidate, exclude_text)
                || fnmatch(&candidate, &format!("{exclude_text}/**"))
            {
                return true;
            }
            continue;
        }
        let resolved_exclude = resolve_nonstrict(exclude_text);
        if candidate == resolved_exclude
            || candidate
                .strip_prefix(resolved_exclude.as_str())
                .is_some_and(|rest| rest.starts_with('/'))
        {
            return true;
        }
    }
    false
}

/// `Path.resolve(strict=False)`: symlinks in the existing prefix are followed, the
/// non-existent suffix is appended lexically with `..` collapsed.
pub fn resolve_nonstrict(path: &str) -> String {
    let p = Path::new(path);
    let abs = if p.is_absolute() {
        p.to_path_buf()
    } else {
        std::env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("/"))
            .join(p)
    };

    let mut resolved = PathBuf::from("/");
    let mut lexical: Vec<String> = Vec::new();
    let mut found_nonexistent = false;
    for component in abs.components() {
        let name = match component {
            Component::Normal(c) => c.to_string_lossy().to_string(),
            Component::ParentDir => "..".to_string(),
            _ => continue,
        };
        if !found_nonexistent {
            match std::fs::canonicalize(resolved.join(&name)) {
                Ok(canonical) => {
                    resolved = canonical;
                    continue;
                }
                Err(_) => found_nonexistent = true,
            }
        }
        if name == ".." {
            if lexical.pop().is_none() {
                resolved.pop();
            }
        } else {
            lexical.push(name);
        }
    }
    let mut out = resolved.to_string_lossy().to_string();
    for name in lexical {
        if !out.ends_with('/') {
            out.push('/');
        }
        out.push_str(&name);
    }
    out
}

/// Python `fnmatch.fnmatchcase`: `*` crosses `/`, `?` is one character, `[seq]`/`[!seq]`
/// with the reversed-range and `[]`/`[!]` quirks of `fnmatch.translate`; whole-string,
/// case-sensitive.
pub fn fnmatch(candidate: &str, pattern: &str) -> bool {
    let s: Vec<char> = candidate.chars().collect();
    let p: Vec<char> = pattern.chars().collect();
    fnmatch_chars(&s, &p)
}

enum Element {
    Star,
    Any,
    Literal(char),
    Set(BracketSet),
}

struct BracketSet {
    negate: bool,
    /// `[!]`-style "negated empty" sets match any character.
    match_any: bool,
    singles: Vec<char>,
    ranges: Vec<(char, char)>,
}

impl BracketSet {
    fn matches(&self, ch: char) -> bool {
        if self.match_any {
            return true;
        }
        let hit =
            self.singles.contains(&ch) || self.ranges.iter().any(|&(lo, hi)| lo <= ch && ch <= hi);
        hit != self.negate
    }
}

fn next_element(p: &[char], pi: usize) -> (Element, usize) {
    match p[pi] {
        '*' => (Element::Star, 1),
        '?' => (Element::Any, 1),
        '[' => match parse_bracket(p, pi) {
            Some((set, consumed)) => (Element::Set(set), consumed),
            None => (Element::Literal('['), 1),
        },
        c => (Element::Literal(c), 1),
    }
}

/// The bracket expression at `p[start] == '['`; `None` when unterminated (a literal `[`).
fn parse_bracket(p: &[char], start: usize) -> Option<(BracketSet, usize)> {
    let n = p.len();
    let i = start + 1;
    let mut j = i;
    if j < n && p[j] == '!' {
        j += 1;
    }
    if j < n && p[j] == ']' {
        j += 1;
    }
    while j < n && p[j] != ']' {
        j += 1;
    }
    if j >= n {
        return None;
    }
    let stuff = &p[i..j];
    let consumed = j + 1 - start;
    let empty = |negate, match_any| BracketSet {
        negate,
        match_any,
        singles: Vec::new(),
        ranges: Vec::new(),
    };
    if stuff.is_empty() {
        return Some((empty(false, false), consumed));
    }
    let (negate, body) = match stuff[0] {
        '!' => (true, &stuff[1..]),
        _ => (false, stuff),
    };
    if negate && body.is_empty() {
        return Some((empty(false, true), consumed));
    }

    let mut singles: Vec<char> = Vec::new();
    let mut ranges: Vec<(char, char)> = Vec::new();
    if !body.contains(&'-') {
        singles.extend_from_slice(body);
    } else {
        // Chunk around range hyphens exactly like translate(): the search for '-'
        // starts after the first body char and skips two chars after each hyphen.
        let mut chunks: Vec<Vec<char>> = Vec::new();
        let mut i = 0usize;
        let mut k = 1usize;
        while k < body.len() {
            match body[k..].iter().position(|&c| c == '-') {
                None => break,
                Some(off) => {
                    let hyphen = k + off;
                    chunks.push(body[i..hyphen].to_vec());
                    i = hyphen + 1;
                    k = hyphen + 3;
                }
            }
        }
        let tail: Vec<char> = body[i.min(body.len())..].to_vec();
        if tail.is_empty() {
            if let Some(last) = chunks.last_mut() {
                last.push('-');
            }
        } else {
            chunks.push(tail);
        }
        // Reversed ranges are removed: both endpoints go and the chunks merge.
        let mut idx = chunks.len();
        while idx > 1 {
            idx -= 1;
            let lo = chunks[idx - 1].last().copied();
            let hi = chunks[idx].first().copied();
            if let (Some(lo), Some(hi)) = (lo, hi) {
                if lo > hi {
                    let rest: Vec<char> = chunks[idx][1..].to_vec();
                    chunks[idx - 1].pop();
                    chunks[idx - 1].extend(rest);
                    chunks.remove(idx);
                }
            }
        }
        // Adjacent chunks are joined by a range: last char of one to first of the next.
        let count = chunks.len();
        for (ci, chunk) in chunks.iter().enumerate() {
            let mut lo_idx = 0usize;
            let mut hi_idx = chunk.len();
            if ci > 0 && !chunk.is_empty() {
                lo_idx = 1;
            }
            if ci + 1 < count && !chunk.is_empty() {
                hi_idx -= 1;
                ranges.push((chunk[hi_idx], chunks[ci + 1][0]));
            }
            if lo_idx <= hi_idx {
                singles.extend_from_slice(&chunk[lo_idx..hi_idx]);
            }
        }
    }
    Some((
        BracketSet {
            negate,
            match_any: false,
            singles,
            ranges,
        },
        consumed,
    ))
}

fn fnmatch_chars(s: &[char], p: &[char]) -> bool {
    let mut si = 0;
    let mut pi = 0;
    let mut star: Option<(usize, usize)> = None;
    while si < s.len() {
        if pi < p.len() {
            let (element, consumed) = next_element(p, pi);
            let matched = match element {
                Element::Star => {
                    star = Some((pi, si));
                    pi += consumed;
                    continue;
                }
                Element::Any => true,
                Element::Literal(c) => c == s[si],
                Element::Set(set) => set.matches(s[si]),
            };
            if matched {
                si += 1;
                pi += consumed;
                continue;
            }
        }
        // Mismatch: retry from the last `*`, letting it absorb one more character.
        match star {
            Some((sp, ss)) => {
                star = Some((sp, ss + 1));
                si = ss + 1;
                pi = sp + 1;
            }
            None => return false,
        }
    }
    while pi < p.len() && p[pi] == '*' {
        pi += 1;
    }
    pi == p.len()
}

/// Python `sorted(Path)` compares the tuple of components, not the joined string.
pub fn python_sort_key(path: &Path) -> Vec<String> {
    path.components()
        .filter_map(|c| match c {
            Component::Normal(s) => Some(s.to_string_lossy().to_string()),
            Component::RootDir => Some("/".to_string()),
            Component::ParentDir => Some("..".to_string()),
            _ => None,
        })
        .collect()
}

#[cfg(test)]
#[path = "excludes_tests.rs"]
mod tests;
