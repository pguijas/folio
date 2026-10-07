//! Rounded boxes with a centred title (rich `Panel`): the init `Detected`
//! and `Ready` panels and the build's `Build output` panel.

use anstyle::Style;

use super::text::{cell_len, center_margin, pad_right, paint, visible_width, Colors, DIM};
use super::Ui;

/// A box around already-styled body lines.
pub struct Panel {
    pub title: Option<String>,
    pub border: Style,
    pub body: Vec<String>,
    /// Cap on the outer width (rich `width` with `expand=False`); the content
    /// decides below it, `expand` without a cap takes the console width.
    pub width: Option<usize>,
    pub expand: bool,
}

impl Panel {
    /// A content-fitted panel with a title.
    pub fn new(title: &str, border: Style, body: Vec<String>) -> Panel {
        Panel {
            title: Some(title.to_string()),
            border,
            body,
            width: None,
            expand: false,
        }
    }

    /// The outer width this panel takes on a `console_width` console.
    pub fn outer_width(&self, console_width: usize) -> usize {
        if self.expand && self.width.is_none() {
            return console_width;
        }
        let widest = self
            .body
            .iter()
            .map(|l| visible_width(l))
            .max()
            .unwrap_or(0);
        let title = self.title.as_ref().map_or(0, |t| cell_len(t) + 2);
        (widest + 4)
            .max(title + 4)
            .min(self.width.unwrap_or(console_width))
    }

    /// The box, one string per row. Body lines wider than the box are
    /// hard-wrapped at the inner width.
    pub fn render(&self, console_width: usize, colors: Colors) -> Vec<String> {
        let width = self.outer_width(console_width);
        let inner = width.saturating_sub(4);
        let bar = |text: &str| paint(self.border, text, colors);
        let mut lines = Vec::with_capacity(self.body.len() + 2);

        let top_rule = match &self.title {
            Some(title) if width > 4 => {
                let title = format!(" {title} ");
                let excess = inner.saturating_sub(cell_len(&title));
                let left = excess / 2;
                format!("─{}{title}{}─", "─".repeat(left), "─".repeat(excess - left))
            }
            _ => "─".repeat(width.saturating_sub(2)),
        };
        lines.push(bar(&format!("╭{top_rule}╮")));
        for line in &self.body {
            for chunk in wrap(line, inner) {
                lines.push(format!(
                    "{} {} {}",
                    bar("│"),
                    pad_right(&chunk, inner),
                    bar("│")
                ));
            }
        }
        lines.push(bar(&format!("╰{}╯", "─".repeat(width.saturating_sub(2)))));
        lines
    }
}

/// Wrap a styled line into chunks of at most `width` visible cells: at the
/// last space when there is one, else a hard cut. Escape sequences travel
/// with the character they precede.
// ponytail: styles are not re-opened on the continuation line (rich did).
fn wrap(line: &str, width: usize) -> Vec<String> {
    if width == 0 || visible_width(line) <= width {
        return vec![line.to_string()];
    }
    let mut chunks = Vec::new();
    let mut current = String::new();
    let mut col = 0;
    // Byte index of the last space in `current` and the column after it.
    let mut last_space: Option<(usize, usize)> = None;
    let mut chars = line.chars().peekable();
    while let Some(c) = chars.next() {
        if c == '\x1b' {
            current.push(c);
            if chars.peek() == Some(&'[') {
                for c in chars.by_ref() {
                    current.push(c);
                    if c.is_ascii_alphabetic() {
                        break;
                    }
                }
            }
            continue;
        }
        let w = unicode_width::UnicodeWidthChar::width(c).unwrap_or(0);
        if col + w > width {
            if c == ' ' {
                chunks.push(std::mem::take(&mut current));
                col = 0;
                last_space = None;
                continue;
            }
            match last_space.take() {
                Some((at, after_space)) => {
                    let rest = current[at + 1..].to_string();
                    current.truncate(at);
                    chunks.push(std::mem::take(&mut current));
                    current = rest;
                    col -= after_space;
                }
                None => {
                    chunks.push(std::mem::take(&mut current));
                    col = 0;
                }
            }
        }
        if c == ' ' {
            last_space = Some((current.len(), col + w));
        }
        current.push(c);
        col += w;
    }
    chunks.push(current);
    chunks
}

/// Prefix every line so a `block_width` block sits centred on the console.
pub fn center_block(lines: Vec<String>, block_width: usize, console_width: usize) -> Vec<String> {
    let margin = " ".repeat(center_margin(block_width, console_width));
    lines.into_iter().map(|l| format!("{margin}{l}")).collect()
}

/// The `Build output` panel: the captured export log, full width, dim border.
pub fn print_build_output(ui: &Ui, lines: &[String]) {
    if lines.is_empty() {
        return;
    }
    let mut body: Vec<String> = lines.iter().map(|l| l.trim_end().to_string()).collect();
    if body.iter().all(|l| l.is_empty()) {
        body = vec!["Waiting for build output...".to_string()];
    }
    let panel = Panel {
        title: Some("Build output".into()),
        border: DIM,
        body,
        width: None,
        expand: true,
    };
    ui.blank();
    ui.print_lines(&panel.render(ui.width, ui.colors));
}

#[cfg(test)]
#[path = "panel_tests.rs"]
mod tests;
