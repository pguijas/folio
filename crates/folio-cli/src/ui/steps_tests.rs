use super::*;
use crate::ui::text::{BOLD, YELLOW};

#[test]
fn count_phrase_pluralises() {
    assert_eq!(count_phrase(1, "module", None), "1 module");
    assert_eq!(count_phrase(3, "module", None), "3 modules");
    assert_eq!(count_phrase(1, "doc page", None), "1 doc page");
    assert_eq!(
        count_phrase(0, "doc page", Some("doc pages")),
        "0 doc pages"
    );
}

#[test]
fn step_rows_pad_the_label_to_twelve_cells() {
    assert_eq!(
        step_line(
            "Sources",
            "3 modules, 12 doc pages",
            "✓",
            GREEN,
            BOLD,
            Colors::Off
        ),
        "✓ Sources      › 3 modules, 12 doc pages"
    );
    assert_eq!(
        step_line("Dependencies", "installed", "✓", GREEN, BOLD, Colors::Off),
        "✓ Dependencies › installed"
    );
    assert_eq!(
            step_line("Links", "2 broken internal links", "!", YELLOW, BOLD_YELLOW, Colors::TrueColor),
            "\x1b[33m!\x1b[0m \x1b[1m\x1b[33mLinks       \x1b[0m \x1b[2m›\x1b[0m 2 broken internal links"
        );
    assert_eq!(
        step_line(
            "Site ready",
            "_site/",
            "✓",
            MAGENTA,
            BOLD_MAGENTA,
            Colors::Off
        ),
        "✓ Site ready   › _site/"
    );
    assert_eq!(
        step_line(
            "Done",
            "4 pages in 1.2s",
            "✓",
            GREEN,
            BOLD_GREEN,
            Colors::Off
        ),
        "✓ Done         › 4 pages in 1.2s"
    );
}

#[test]
fn spinner_is_inert_without_a_tty() {
    let ui = Ui {
        colors: Colors::Off,
        tty: false,
        width: 80,
    };
    let spinner = Spinner::start(&ui, "Pages", "generating content", Some(3));
    spinner.advance(1);
    assert!(spinner.handle.is_none());
}
