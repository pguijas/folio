use super::*;

#[test]
fn paint_is_the_bare_text_without_colour() {
    assert_eq!(paint(RED, "x", Colors::Off), "x");
    assert_eq!(paint(PLAIN, "x", Colors::TrueColor), "x");
    assert_eq!(paint(RED, "x", Colors::TrueColor), "\x1b[31mx\x1b[0m");
    assert_eq!(
        paint(bold_rgb(0xc4, 0xb5, 0xfd), "y", Colors::TrueColor),
        "\x1b[1m\x1b[38;2;196;181;253my\x1b[0m"
    );
    assert_eq!(
        paint(bold_rgb(0xc4, 0xb5, 0xfd), "y", Colors::Ansi256),
        "\x1b[1m\x1b[38;5;183my\x1b[0m"
    );
    assert_eq!(paint(RED, "x", Colors::Ansi256), "\x1b[31mx\x1b[0m");
}

#[test]
fn rgb_downgrades_to_the_nearest_palette_entry() {
    for ((r, g, b), index) in [
        ((0xc4, 0xb5, 0xfd), 183),
        ((0xbe, 0xf2, 0x64), 155),
        ((0xbf, 0xdb, 0xfe), 153),
        ((0xf8, 0xfa, 0xfc), 231),
        ((0x80, 0x80, 0x80), 244),
        ((0, 0, 0), 16),
        ((255, 255, 255), 231),
    ] {
        assert_eq!(
            nearest_ansi256(RgbColor(r, g, b)),
            index,
            "#{r:02x}{g:02x}{b:02x}"
        );
    }
}

#[test]
fn visible_width_skips_escapes_and_counts_cells() {
    assert_eq!(visible_width("\x1b[1mab\x1b[0m"), 2);
    assert_eq!(visible_width("╭─╮"), 3);
    assert_eq!(visible_width("日本"), 4);
    assert_eq!(pad_right("\x1b[2mab\x1b[0m", 4), "\x1b[2mab\x1b[0m  ");
    assert_eq!(center_margin(48, 80), 16);
    assert_eq!(center_margin(90, 80), 0);
}

#[test]
fn merge_layers_effects_and_foreground() {
    let merged = merge(CYAN, BOLD);
    assert_eq!(merged, CYAN.bold());
    let merged = merge(CYAN, GREEN.bold());
    assert_eq!(merged, GREEN.bold());
}
