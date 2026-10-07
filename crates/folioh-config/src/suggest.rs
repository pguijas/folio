//! The did-you-mean an "unknown key" or "must be one of" message adds.

/// `text` lowercased with `_` and `-` dropped, so `darkMode`, `dark-mode`
/// and `dark_mode` compare equal.
fn fold(text: &str) -> Vec<char> {
    text.chars()
        .filter(|c| *c != '_' && *c != '-')
        .flat_map(char::to_lowercase)
        .collect()
}

fn edit_distance(a: &[char], b: &[char]) -> usize {
    let mut previous: Vec<usize> = (0..=b.len()).collect();
    for (i, ca) in a.iter().enumerate() {
        let mut current = vec![i + 1; b.len() + 1];
        for (j, cb) in b.iter().enumerate() {
            let substitution = previous[j] + usize::from(ca != cb);
            current[j + 1] = substitution.min(previous[j + 1] + 1).min(current[j] + 1);
        }
        previous = current;
    }
    previous[b.len()]
}

/// The candidate `input` most likely misspells: case, `_` and `-` ignored,
/// within one edit for words of four letters or fewer and two otherwise.
/// Ties go to the earlier candidate.
pub fn closest_match<'a>(
    input: &str,
    candidates: impl IntoIterator<Item = &'a str>,
) -> Option<&'a str> {
    let wanted = fold(input);
    let limit = if wanted.len() <= 4 { 1 } else { 2 };
    let mut best: Option<(usize, &'a str)> = None;
    for candidate in candidates {
        let distance = edit_distance(&wanted, &fold(candidate));
        if distance <= limit && best.is_none_or(|(d, _)| distance < d) {
            best = Some((distance, candidate));
        }
    }
    best.map(|(_, candidate)| candidate)
}

/// `" (did you mean 'x'?)"` when a candidate is near `input`, else `""`.
pub fn did_you_mean<'a>(input: &str, candidates: impl IntoIterator<Item = &'a str>) -> String {
    closest_match(input, candidates)
        .map(|near| format!(" (did you mean '{near}'?)"))
        .unwrap_or_default()
}

#[cfg(test)]
#[path = "suggest_tests.rs"]
mod tests;
