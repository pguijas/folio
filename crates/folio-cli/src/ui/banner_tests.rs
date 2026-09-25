use super::*;

#[test]
fn the_art_is_six_lines_of_39_cells() {
    let lines: Vec<&str> = FOLIO_ASCII_ART.lines().collect();
    assert_eq!(lines.len(), 6);
    for line in lines {
        assert_eq!(cell_len(line), 39, "{line:?}");
    }
}

#[test]
fn banner_centres_the_art_and_appends_the_version() {
    let lines = banner("v0.3.0-a1", Some(80), None, Colors::Off);
    assert_eq!(lines.len(), 6);
    assert!(lines.iter().all(|l| l.starts_with(&" ".repeat(20))));
    assert!(lines[0].ends_with("██████╗ "));
    assert!(lines[5].ends_with("╚═════╝  v0.3.0-a1"));

    let plain = banner("", None, None, Colors::Off);
    assert_eq!(plain[0], " ████████╗ ██████╗ ██╗     ██╗ ██████╗ ");
}

#[test]
fn banner_with_news_adds_a_blank_and_the_centred_item() {
    let lines = banner("v1", Some(80), Some(FOLIO_NEWS_ITEMS[1]), Colors::TrueColor);
    assert_eq!(lines.len(), 8);
    assert_eq!(lines[6], "");
    let text = "· Pagefind search opens from the navbar or Cmd+K ·";
    let margin = (80 - cell_len(text)) / 2;
    assert_eq!(
        lines[7],
        format!(
            "\x1b[1m\x1b[38;2;190;242;100m{}{text}\x1b[0m",
            " ".repeat(margin)
        )
    );
    assert!(lines[0].starts_with("\x1b[1m\x1b[38;2;196;181;253m"));
}

#[test]
fn news_item_rotates_once_per_interval() {
    assert_eq!(news_item(0.0, 1.0), FOLIO_NEWS_ITEMS[0]);
    assert_eq!(news_item(1.9, 1.0), FOLIO_NEWS_ITEMS[1]);
    assert_eq!(news_item(12.0, 1.0), FOLIO_NEWS_ITEMS[0]);
    assert_eq!(news_item(-5.0, 1.0), FOLIO_NEWS_ITEMS[0]);
    assert_eq!(news_item(5.0, 2.0), FOLIO_NEWS_ITEMS[2]);
    assert!(FOLIO_NEWS_ITEMS.contains(&current_news_item()));
}
