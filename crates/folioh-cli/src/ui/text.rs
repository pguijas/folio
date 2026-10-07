//! Styled text over `anstyle` and cell widths over `unicode-width`: the colours
//! and styles every terminal line is drawn with.

use anstyle::{Ansi256Color, AnsiColor, Color, RgbColor, Style};
use unicode_width::UnicodeWidthStr;

/// A truecolor foreground.
pub const fn rgb(r: u8, g: u8, b: u8) -> Style {
    Style::new().fg_color(Some(Color::Rgb(RgbColor(r, g, b))))
}

/// A bold truecolor foreground (rich `bold #rrggbb`).
pub const fn bold_rgb(r: u8, g: u8, b: u8) -> Style {
    rgb(r, g, b).bold()
}

const fn ansi(color: AnsiColor) -> Style {
    Style::new().fg_color(Some(Color::Ansi(color)))
}

/// No style.
pub const PLAIN: Style = Style::new();
/// Bold.
pub const BOLD: Style = Style::new().bold();
/// Dim.
pub const DIM: Style = Style::new().dimmed();
/// Italic (table titles).
pub const ITALIC: Style = Style::new().italic();
/// ANSI red (errors).
pub const RED: Style = ansi(AnsiColor::Red);
/// ANSI green (`✓`, `Cleaned:`).
pub const GREEN: Style = ansi(AnsiColor::Green);
/// ANSI yellow (warnings).
pub const YELLOW: Style = ansi(AnsiColor::Yellow);
/// ANSI cyan (the coverage module column).
pub const CYAN: Style = ansi(AnsiColor::Cyan);
/// Bold cyan (spinner labels, the prompt default).
pub const BOLD_CYAN: Style = CYAN.bold();
/// Dim yellow (the init abort line).
pub const DIM_YELLOW: Style = YELLOW.dimmed();

/// Terminal cells a string occupies (box-drawing glyphs are 1, CJK 2).
pub fn cell_len(text: &str) -> usize {
    text.width()
}

/// How much colour the terminal gets: none, the 256-colour palette, or
/// 24-bit. Decided once by `Ui::detect`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Colors {
    Off,
    Ansi256,
    TrueColor,
}

/// The 256-colour palette entry nearest an RGB value: the 6x6x6 cube or
/// one of the 24 greys, whichever is closer (rich's downgrade).
pub fn nearest_ansi256(RgbColor(r, g, b): RgbColor) -> u8 {
    const LEVELS: [u8; 6] = [0, 95, 135, 175, 215, 255];
    let distance = |a: (u8, u8, u8), b: (u8, u8, u8)| {
        [(a.0, b.0), (a.1, b.1), (a.2, b.2)]
            .iter()
            .map(|(x, y)| (i32::from(*x) - i32::from(*y)).pow(2))
            .sum::<i32>()
    };
    let nearest = |v: u8| {
        LEVELS
            .iter()
            .enumerate()
            .min_by_key(|(_, level)| (i32::from(**level) - i32::from(v)).abs())
            .map(|(index, level)| (index as u8, *level))
            .unwrap_or((0, 0))
    };
    let ((ri, rl), (gi, gl), (bi, bl)) = (nearest(r), nearest(g), nearest(b));
    let cube = 16 + 36 * ri + 6 * gi + bi;
    let average = (i32::from(r) + i32::from(g) + i32::from(b)) / 3;
    let grey_index = ((average - 8 + 5) / 10).clamp(0, 23);
    let grey = (8 + 10 * grey_index) as u8;
    if distance((r, g, b), (grey, grey, grey)) < distance((r, g, b), (rl, gl, bl)) {
        232 + grey_index as u8
    } else {
        cube
    }
}

fn downgrade(style: Style) -> Style {
    match style.get_fg_color() {
        Some(Color::Rgb(rgb)) => {
            style.fg_color(Some(Color::Ansi256(Ansi256Color(nearest_ansi256(rgb)))))
        }
        _ => style,
    }
}

/// `text` wrapped in `style` at the terminal's colour depth; the bare text
/// when colour is off.
pub fn paint(style: Style, text: &str, colors: Colors) -> String {
    let style = match colors {
        Colors::Off => return text.to_string(),
        Colors::TrueColor => style,
        Colors::Ansi256 => downgrade(style),
    };
    if style.is_plain() {
        return text.to_string();
    }
    format!("{}{text}{}", style.render(), style.render_reset())
}

/// `base` with `over`'s effects added and its foreground, when set, on top.
pub fn merge(base: Style, over: Style) -> Style {
    let mut style = base.effects(base.get_effects() | over.get_effects());
    if let Some(fg) = over.get_fg_color() {
        style = style.fg_color(Some(fg));
    }
    style
}

/// Visible cells of a string that may carry SGR escape sequences.
pub fn visible_width(text: &str) -> usize {
    let mut width = 0;
    let mut chars = text.chars();
    while let Some(c) = chars.next() {
        if c == '\x1b' {
            // CSI ... final byte; other escapes are one char.
            if chars.next() == Some('[') {
                for c in chars.by_ref() {
                    if c.is_ascii_alphabetic() {
                        break;
                    }
                }
            }
            continue;
        }
        width += unicode_width::UnicodeWidthChar::width(c).unwrap_or(0);
    }
    width
}

/// Right-pad `text` with spaces to `width` visible cells.
pub fn pad_right(text: &str, width: usize) -> String {
    let current = visible_width(text);
    if current >= width {
        return text.to_string();
    }
    format!("{text}{}", " ".repeat(width - current))
}

/// Spaces that centre a `content_width`-cell block inside `width` cells
/// (rich puts the odd cell on the right).
pub fn center_margin(content_width: usize, width: usize) -> usize {
    width.saturating_sub(content_width) / 2
}

#[cfg(test)]
#[path = "text_tests.rs"]
mod tests;
