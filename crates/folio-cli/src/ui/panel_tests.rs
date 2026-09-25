use super::*;
use crate::ui::text::{rgb, PLAIN};

#[test]
fn a_fitted_panel_centres_its_title_in_the_top_rule() {
    let body = vec![
        "Target     .".to_string(),
        "Status     Documentation scaffold not found".to_string(),
    ];
    let panel = Panel::new("Detected", PLAIN, body);
    let lines = panel.render(80, Colors::Off);
    assert_eq!(panel.outer_width(80), 47);
    assert_eq!(
        lines[0],
        format!("╭{} Detected {}╮", "─".repeat(17), "─".repeat(18))
    );
    assert_eq!(lines[1], format!("│ Target     .{} │", " ".repeat(31)));
    assert_eq!(lines[2], "│ Status     Documentation scaffold not found │");
    assert_eq!(lines[3], format!("╰{}╯", "─".repeat(45)));
    assert!(lines.iter().all(|l| cell_len(l) == 47));

    let centred = center_block(lines, 47, 80);
    assert!(centred[0].starts_with(&" ".repeat(16)));
    assert_eq!(centred[0].chars().nth(16), Some('╭'));
}

#[test]
fn a_capped_panel_hugs_its_content_and_puts_the_odd_cell_on_the_right() {
    let panel = Panel {
        title: Some("Ready".into()),
        border: rgb(0xa7, 0x8b, 0xfa),
        body: vec!["✓ Documentation project ready.".into(), String::new()],
        width: Some(78),
        expand: false,
    };
    let lines = panel.render(80, Colors::Off);
    assert_eq!(panel.outer_width(80), 34, "the cap is not a fixed width");
    assert_eq!(
        lines[0],
        format!("╭{} Ready {}╮", "─".repeat(12), "─".repeat(13))
    );
    assert_eq!(lines[1], "│ ✓ Documentation project ready. │");
    assert_eq!(lines[2], format!("│{}│", " ".repeat(32)));
    assert!(lines.iter().all(|l| cell_len(l) == 34));

    let coloured = panel.render(80, Colors::TrueColor);
    assert!(coloured[1].starts_with("\x1b[38;2;167;139;250m│\x1b[0m ✓"));

    // The cap wraps what does not fit; a title never overflows its rule.
    let capped = Panel {
        width: Some(20),
        ..panel
    };
    assert_eq!(capped.outer_width(80), 20);
    assert_eq!(capped.render(80, Colors::Off).len(), 5);
    let tiny = Panel::new("Ready", PLAIN, vec!["x".into()]);
    assert_eq!(tiny.outer_width(80), 11);
    assert_eq!(tiny.render(80, Colors::Off)[0], "╭─ Ready ─╮");
}

#[test]
fn overlong_lines_wrap_inside_the_box() {
    let panel = Panel {
        title: None,
        border: PLAIN,
        body: vec!["abcdefgh".into()],
        width: Some(8),
        expand: false,
    };
    let lines = panel.render(80, Colors::Off);
    assert_eq!(lines, vec!["╭──────╮", "│ abcd │", "│ efgh │", "╰──────╯"]);
    assert_eq!(wrap("\x1b[1mabc\x1b[0m", 2), vec!["\x1b[1mab", "c\x1b[0m"]);
    assert_eq!(wrap("hello wide world", 8), vec!["hello", "wide", "world"]);
    assert_eq!(
        wrap("Created demo/very-long-name", 12),
        vec!["Created", "demo/very-lo", "ng-name"]
    );
    assert_eq!(
        wrap("ab \x1b[1mcd\x1b[0m ef", 5),
        vec!["ab \x1b[1mcd\x1b[0m", "ef"]
    );
}
