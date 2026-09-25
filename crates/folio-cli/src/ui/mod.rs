//! Everything the binary prints: colour policy decided once, terminal width,
//! the banner, step rows, panels, tables and the init selector.

pub mod banner;
pub mod panel;
pub mod select;
pub mod steps;
pub mod table;
pub mod text;

use std::io::{self, IsTerminal, Write};

use anstream::ColorChoice;
use anstyle::Style;

use text::{paint, Colors};

/// The terminal as the binary sees it. Decided once at startup.
pub struct Ui {
    /// Colour depth: off unless stdout is a TTY without `NO_COLOR` (or a force
    /// switch is set); 24-bit only when `COLORTERM` says so.
    pub colors: Colors,
    /// Stdout is a terminal (spinners and the ticker stay silent otherwise).
    pub tty: bool,
    /// Console columns: `COLUMNS`, else the terminal size, else 80.
    pub width: usize,
}

impl Ui {
    /// Read the terminal once: colour depth and width.
    pub fn detect() -> Ui {
        let stdout = io::stdout();
        let tty = stdout.is_terminal();
        // anstream reads NO_COLOR, CLICOLOR_FORCE and the TTY; rich also
        // honoured FORCE_COLOR, so keep that switch.
        let non_empty = |name: &str| std::env::var_os(name).is_some_and(|v| !v.is_empty());
        let color = anstream::AutoStream::choice(&stdout) != ColorChoice::Never
            || (non_empty("FORCE_COLOR") && !non_empty("NO_COLOR"));
        let truecolor = std::env::var("COLORTERM").is_ok_and(|v| {
            matches!(
                v.trim().to_ascii_lowercase().as_str(),
                "truecolor" | "24bit"
            )
        });
        let colors = match (color, truecolor) {
            (false, _) => Colors::Off,
            (true, true) => Colors::TrueColor,
            (true, false) => Colors::Ansi256,
        };
        let width = std::env::var("COLUMNS")
            .ok()
            .and_then(|v| v.trim().parse::<usize>().ok())
            .filter(|w| *w > 0)
            .or_else(|| {
                tty.then(|| {
                    crossterm::terminal::size()
                        .ok()
                        .map(|(cols, _)| cols as usize)
                })
                .flatten()
            })
            .unwrap_or(80);
        Ui { colors, tty, width }
    }

    /// `text` styled for this terminal.
    pub fn styled(&self, style: Style, text: &str) -> String {
        paint(style, text, self.colors)
    }

    /// One line on stdout (a broken pipe is not an error worth reporting).
    pub fn print(&self, text: &str) {
        let mut out = io::stdout().lock();
        let _ = writeln!(out, "{text}");
    }

    /// One styled line on stdout.
    pub fn print_styled(&self, style: Style, text: &str) {
        self.print(&self.styled(style, text));
    }

    /// One line on stderr: diagnostics, so a caller can separate them from output.
    pub fn eprint(&self, text: &str) {
        let mut err = io::stderr().lock();
        let _ = writeln!(err, "{text}");
    }

    /// One styled line on stderr.
    pub fn eprint_styled(&self, style: Style, text: &str) {
        self.eprint(&self.styled(style, text));
    }

    /// Several lines on stdout under one lock.
    pub fn print_lines(&self, lines: &[String]) {
        let mut out = io::stdout().lock();
        for line in lines {
            let _ = writeln!(out, "{line}");
        }
    }

    /// An empty line.
    pub fn blank(&self) {
        self.print("");
    }
}
