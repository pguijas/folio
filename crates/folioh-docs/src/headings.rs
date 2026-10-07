//! Docstring headings under the item they document. A docstring's `# Examples`
//! is written for its own page; on a module page it would open a new H1 in the
//! middle of an item, so every ATX heading outside a code fence moves down
//! until the shallowest one sits at `floor`, never past H6.

/// `text` with its headings shifted so the shallowest is at least `floor`.
pub(crate) fn shift_headings(text: &str, floor: usize) -> String {
    let lines: Vec<&str> = text.split('\n').collect();
    let levels = outside_fences(&lines);
    let Some(shallowest) = levels.iter().flatten().min().copied() else {
        return text.to_string();
    };
    if shallowest >= floor {
        return text.to_string();
    }
    let by = floor - shallowest;
    lines
        .iter()
        .zip(&levels)
        .map(|(line, level)| match level {
            Some(level) => {
                let hashes_at = line.len() - line.trim_start().len();
                let rest = &line[hashes_at + level..];
                format!(
                    "{}{}{rest}",
                    &line[..hashes_at],
                    "#".repeat((level + by).min(6))
                )
            }
            None => (*line).to_string(),
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// The ATX heading level of every line outside a fenced code block.
fn outside_fences(lines: &[&str]) -> Vec<Option<usize>> {
    let mut fence: Option<(char, usize)> = None;
    lines
        .iter()
        .map(|line| {
            let indent = line.len() - line.trim_start_matches(' ').len();
            let body = line.trim_start_matches(' ');
            let marker = body.chars().next().filter(|c| *c == '`' || *c == '~');
            let run = marker.map_or(0, |c| body.chars().take_while(|x| *x == c).count());
            if indent <= 3 && run >= 3 {
                let c = marker.expect("a run has a marker");
                match fence {
                    None => fence = Some((c, run)),
                    Some((open, len)) if open == c && run >= len && body.trim() == &body[..run] => {
                        fence = None
                    }
                    Some(_) => {}
                }
                return None;
            }
            if fence.is_some() || indent > 3 {
                return None;
            }
            let level = body.chars().take_while(|c| *c == '#').count();
            let after = body[level..].chars().next();
            ((1..=6).contains(&level) && after.is_none_or(|c| c == ' ' || c == '\t'))
                .then_some(level)
        })
        .collect()
}

#[cfg(test)]
#[path = "headings_tests.rs"]
mod tests;
