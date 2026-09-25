//! The Folio ASCII banner and its rotating news line.

use std::time::{SystemTime, UNIX_EPOCH};

use anstyle::Style;

use super::text::{bold_rgb, cell_len, center_margin, paint, Colors};

/// The art lines: bold `#c4b5fd`.
pub const FOLIO_LOGO_STYLE: Style = bold_rgb(0xc4, 0xb5, 0xfd);
/// The news line: bold `#bef264`.
pub const FOLIO_NEWS_STYLE: Style = bold_rgb(0xbe, 0xf2, 0x64);

/// The twelve news items, rotated once per second.
pub const FOLIO_NEWS_ITEMS: [&str; 12] = [
    "Incremental builds skip pages whose sources are unchanged",
    "Pagefind search opens from the navbar or Cmd+K",
    "GitHub Pages deploys infer the right base path",
    "Theme presets ship polished docs shells by default",
    "Mermaid diagrams render from fenced code blocks",
    "KaTeX math works inline and in display blocks",
    "Coverage gates catch undocumented public APIs",
    "Source links jump straight to GitHub file lines",
    "llms.txt output keeps docs readable for AI assistants",
    "Link validation flags broken internal links at build time",
    "File watching rebuilds changed pages while serving",
    "Social cards generate OpenGraph previews automatically",
];

/// Six lines, 39 cells each, leading and trailing space included.
pub const FOLIO_ASCII_ART: &str = concat!(
    " ████████╗ ██████╗ ██╗     ██╗ ██████╗ \n",
    " ██╔═════╝██╔═══██╗██║     ██║██╔═══██╗\n",
    " █████╗   ██║   ██║██║     ██║██║   ██║\n",
    " ██╔══╝   ██║   ██║██║     ██║██║   ██║\n",
    " ██║      ╚██████╔╝███████╗██║╚██████╔╝\n",
    " ╚═╝       ╚═════╝ ╚══════╝╚═╝ ╚═════╝ "
);

/// The news item shown after `elapsed_secs`, one per `interval` seconds.
pub fn news_item(elapsed_secs: f64, interval: f64) -> &'static str {
    let index = (elapsed_secs.max(0.0) / interval) as usize;
    FOLIO_NEWS_ITEMS[index % FOLIO_NEWS_ITEMS.len()]
}

/// The item for the current wall-clock second: the same in every process.
pub fn current_news_item() -> &'static str {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0);
    news_item(secs, 1.0)
}

fn center(line: &str, width: Option<usize>) -> String {
    match width {
        Some(width) => format!("{}{line}", " ".repeat(center_margin(cell_len(line), width))),
        None => line.to_string(),
    }
}

/// The plain `· item ·` line, centred in `width`; callers style it.
pub fn news_line(width: Option<usize>, item: Option<&str>) -> String {
    let item = item.unwrap_or_else(|| current_news_item());
    center(&format!("· {item} ·"), width)
}

/// The styled banner lines: six art lines (the version on the last), and
/// with `news` a blank line plus the news line.
pub fn banner(
    version: &str,
    width: Option<usize>,
    news: Option<&str>,
    colors: Colors,
) -> Vec<String> {
    let mut lines: Vec<String> = FOLIO_ASCII_ART.lines().map(str::to_string).collect();
    if let Some(width) = width {
        let art_width = lines.iter().map(|l| cell_len(l)).max().unwrap_or(0);
        let pad = " ".repeat(center_margin(art_width, width));
        for line in &mut lines {
            *line = format!("{pad}{line}");
        }
    }
    if !version.is_empty() {
        if let Some(last) = lines.last_mut() {
            *last = format!("{last} {version}");
        }
    }
    let mut out: Vec<String> = lines
        .iter()
        .map(|line| paint(FOLIO_LOGO_STYLE, line, colors))
        .collect();
    if let Some(item) = news {
        out.push(String::new());
        out.push(paint(
            FOLIO_NEWS_STYLE,
            &news_line(width, Some(item)),
            colors,
        ));
    }
    out
}

#[cfg(test)]
#[path = "banner_tests.rs"]
mod tests;
