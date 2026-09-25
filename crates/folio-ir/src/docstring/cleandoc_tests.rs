use super::cleandoc;

#[test]
fn cleandoc_table() {
    let cases = [
        ("Hello world", "Hello world"),
        ("  Hello\n  World", "Hello\nWorld"),
        ("Hello\n    World\n    Foo", "Hello\nWorld\nFoo"),
        ("", ""),
        ("   ", ""),
        ("Hello\n\tWorld", "Hello\nWorld"),
        ("\tFirst\n\t\tSecond", "First\nSecond"),
        ("Doc\ttab\n\n      more\n    ", "Doc     tab\n\nmore"),
        (
            "\n    Leading blank.\n\n    Body.\n\n    ",
            "Leading blank.\n\nBody.",
        ),
        ("Raw \\n stays.", "Raw \\n stays."),
        (
            "Esc \n newline \t tab \u{2014} named.",
            "Esc \nnewline         tab \u{2014} named.",
        ),
        (
            "\u{a0}NBSP-indented\n    \u{a0}line two\n    ",
            "NBSP-indented\nline two",
        ),
        ("Line1\n    Line2\n    ", "Line1\nLine2"),
        (
            "Tab\tafter text\n\tTab-indented line\n    ",
            "Tab     after text\nTab-indented line",
        ),
        // A line with less indent loses `margin` characters of content and
        // the final whitespace-only line survives (fixture 378).
        (
            "First line\n  less indented\n        more indented\n    ",
            "First line\nless indented\n      more indented\n  ",
        ),
        // The margin counts characters, not bytes.
        ("Doc\n\u{a0}\u{a0}x\n   \u{a0}y", "Doc\nx\n \u{a0}y"),
        // Idempotent.
        ("Leading blank.\n\nBody.", "Leading blank.\n\nBody."),
    ];
    for (input, expected) in cases {
        assert_eq!(cleandoc(input), expected, "cleandoc({input:?})");
    }
}
