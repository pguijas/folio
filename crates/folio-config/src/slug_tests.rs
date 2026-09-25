use super::{slug_label, slugify, title_case};

#[test]
fn slugify_matches_the_python_rule() {
    for (input, expected) in [
        ("In progress", "in-progress"),
        ("v1.2 API", "v1-2-api"),
        ("Ünïcode", "ünïcode"),
        ("  Hello__World  ", "hello-world"),
        ("a---b", "a-b"),
        ("-lead and trail-", "lead-and-trail"),
        ("Foo/Bar (baz)!", "foobar-baz"),
        ("", ""),
    ] {
        assert_eq!(slugify(input), expected, "slugify({input:?})");
    }
}

#[test]
fn title_case_keeps_punctuation() {
    for (text, expected) in [
        ("cobol", "Cobol"),
        ("objective-c", "Objective-C"),
        ("a1b MIXED-case_x", "A1B Mixed-Case_X"),
        ("v0.1", "V0.1"),
    ] {
        assert_eq!(title_case(text), expected, "{text}");
    }
}

#[test]
fn slug_label_breaks_words_on_dash_and_underscore() {
    for (slug, expected) in [
        ("ocean-blue", "Ocean Blue"),
        ("common_errors", "Common Errors"),
        ("cookie_caper-api", "Cookie Caper Api"),
        ("v2 API", "V2 Api"),
        ("p2pfl_ws", "P2Pfl Ws"),
        ("api2go", "Api2Go"),
        ("don't-stop", "Don'T Stop"),
    ] {
        assert_eq!(slug_label(slug), expected, "{slug}");
    }
}
