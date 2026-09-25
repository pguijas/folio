//! Step rows (`✓ Label        › detail`), detail rows and the transient
//! spinner row shown while a phase runs.

use std::io::{self, Write};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::Duration;

use anstyle::Style;

use super::text::{cell_len, paint, Colors, BOLD_CYAN, DIM, GREEN, YELLOW};
use super::Ui;

/// Step-row styles: `! Links` in yellow, `Done` in green, `Site ready` in magenta.
pub const MAGENTA: Style =
    Style::new().fg_color(Some(anstyle::Color::Ansi(anstyle::AnsiColor::Magenta)));
/// The `Done` label.
pub const BOLD_GREEN: Style = GREEN.bold();
/// The `! Links` label.
pub const BOLD_YELLOW: Style = YELLOW.bold();
/// The `Site ready` label.
pub const BOLD_MAGENTA: Style = MAGENTA.bold();

const LABEL_WIDTH: usize = 12;
const FRAMES: [&str; 10] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

/// `1 module`, `2 modules`; the plural is `{singular}s` unless given.
pub fn count_phrase(n: usize, singular: &str, plural: Option<&str>) -> String {
    if n == 1 {
        format!("{n} {singular}")
    } else {
        match plural {
            Some(plural) => format!("{n} {plural}"),
            None => format!("{n} {singular}s"),
        }
    }
}

fn padded(label: &str) -> String {
    format!(
        "{label}{}",
        " ".repeat(LABEL_WIDTH.saturating_sub(cell_len(label)))
    )
}

/// `{marker} {label:<12} › {detail}` with the given styles.
pub fn step_line(
    label: &str,
    detail: &str,
    marker: &str,
    marker_style: Style,
    label_style: Style,
    colors: Colors,
) -> String {
    format!(
        "{} {} {} {detail}",
        paint(marker_style, marker, colors),
        paint(label_style, &padded(label), colors),
        paint(DIM, "›", colors)
    )
}

/// A completed step: `✓` green, bold label by default.
pub fn step(
    ui: &Ui,
    label: &str,
    detail: &str,
    marker: &str,
    marker_style: Style,
    label_style: Style,
) {
    ui.print(&step_line(
        label,
        detail,
        marker,
        marker_style,
        label_style,
        ui.colors,
    ));
}

/// A sub-detail row: two spaces then the styled detail (dim or yellow).
pub fn step_detail(ui: &Ui, detail: &str, style: Style) {
    ui.print(&format!("  {}", ui.styled(style, detail)));
}

/// The transient progress row: an animated glyph plus `label › detail`,
/// erased when dropped so the permanent step row takes its place. Silent
/// when stdout is not a terminal.
pub struct Spinner {
    stop: Arc<AtomicBool>,
    done: Arc<AtomicUsize>,
    handle: Option<JoinHandle<()>>,
}

impl Spinner {
    /// Show the row until the guard drops; `total` adds a progress bar.
    pub fn start(ui: &Ui, label: &str, detail: &str, total: Option<usize>) -> Spinner {
        let stop = Arc::new(AtomicBool::new(false));
        let done = Arc::new(AtomicUsize::new(0));
        if !ui.tty {
            return Spinner {
                stop,
                done,
                handle: None,
            };
        }
        let colors = ui.colors;
        let text = format!(
            "{} {} {detail}",
            paint(BOLD_CYAN, &padded(label), colors),
            paint(DIM, "›", colors)
        );
        let (stop_flag, done_count) = (Arc::clone(&stop), Arc::clone(&done));
        let handle = thread::spawn(move || {
            let mut frame = 0;
            while !stop_flag.load(Ordering::Relaxed) {
                let mut line = format!(
                    "{} {text}",
                    paint(GREEN, FRAMES[frame % FRAMES.len()], colors)
                );
                if let Some(total) = total.filter(|t| *t > 0) {
                    let done = done_count.load(Ordering::Relaxed).min(total);
                    let filled = done * 20 / total;
                    line.push_str(&format!(
                        " {}{} {:>3}%",
                        paint(MAGENTA, &"━".repeat(filled), colors),
                        paint(DIM, &"━".repeat(20 - filled), colors),
                        done * 100 / total
                    ));
                }
                let mut out = io::stdout().lock();
                let _ = write!(out, "\r\x1b[2K{line}");
                let _ = out.flush();
                drop(out);
                frame += 1;
                thread::sleep(Duration::from_millis(80));
            }
            let mut out = io::stdout().lock();
            let _ = write!(out, "\r\x1b[2K");
            let _ = out.flush();
        });
        Spinner {
            stop,
            done,
            handle: Some(handle),
        }
    }

    /// Advance the progress bar (Pages: one per page).
    pub fn advance(&self, n: usize) {
        self.done.fetch_add(n, Ordering::Relaxed);
    }
}

impl Drop for Spinner {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
    }
}

#[cfg(test)]
#[path = "steps_tests.rs"]
mod tests;
