use super::*;

#[test]
fn headings_move_below_the_floor_keeping_their_order() {
    assert_eq!(
        shift_headings("Intro.\n\n# Examples\n\ntext\n\n## Detail\n", 3),
        "Intro.\n\n### Examples\n\ntext\n\n#### Detail\n"
    );
}

#[test]
fn headings_already_deep_enough_and_fenced_lines_stay() {
    let deep = "#### Deep\n";
    assert_eq!(shift_headings(deep, 3), deep);
    assert_eq!(
        shift_headings("# Panics\n\n```\n# hidden\n```\n~~~\n# also code\n~~~\n", 2),
        "## Panics\n\n```\n# hidden\n```\n~~~\n# also code\n~~~\n"
    );
}

#[test]
fn a_hash_without_a_space_is_no_heading_and_h6_is_the_last_level() {
    assert_eq!(shift_headings("#tag and #1\n", 4), "#tag and #1\n");
    assert_eq!(shift_headings("# A\n##### E\n", 3), "### A\n###### E\n");
}
