use super::*;
use crate::page::parse_markdown;

#[test]
fn fence_info_strings_survive_and_code_is_never_escaped() {
    let cases: &[(&str, &[&str])] = &[
            ("```python {2,4-6}\nimport os\nimport sys\n```", &["```python {2,4-6}"]),
            ("```python {3}\nline1\nline2\nline3\n```", &["```python {3}"]),
            ("```python {1-5}\nline1\nline2\nline3\nline4\nline5\n```", &["```python {1-5}"]),
            ("```js {1,3-5,7}\ncode\n```", &["```js {1,3-5,7}"]),
            (
                "Text with {braces} here.\n\n```python {2}\nimport os\nimport sys\n```\n\nMore {braces}.",
                &["\\{braces\\}", "```python {2}"],
            ),
            ("```python\nmy_dict = {\"key\": \"value\"}\n```", &["{\"key\": \"value\"}"]),
            ("````markdown\n```python\nd = {\"k\": 1}\n```\n````", &["d = {\"k\": 1}"]),
            ("~~~python\nd = {\"k\": 1}\n~~~", &["d = {\"k\": 1}"]),
            ("1. Step:\n\n   ```python\n   d = {\"k\": 1}\n   ```\n", &["d = {\"k\": 1}"]),
            ("Math $x_{i}$ and code `{y}` and {z}.", &["$x_{i}$", "`{y}`", "\\{z\\}"]),
            ("````markdown\n```python\nx = {1}\n```\n````\n\nProse {brace}.", &["x = {1}", "Prose \\{brace\\}."]),
            ("```python filename=\"main.py\"\nimport os\n```", &["```python filename=\"main.py\""]),
            (
                "```python showLineNumbers {2,4}\nimport os\nimport sys\nfrom pathlib import Path\ndef main(): pass\n```",
                &["```python showLineNumbers {2,4}"],
            ),
            ("The formula $\\frac{a}{b}$ is useful", &["$\\frac{a}{b}$"]),
            ("$$\nx = \\frac{-b}{2a}\n$$", &["\\frac{-b}{2a}"]),
            ("Use dict {key: value} syntax", &["\\{key: value\\}"]),
            ("Set $\\frac{a}{b}$ and use {config}", &["$\\frac{a}{b}$", "\\{config\\}"]),
            ("Both $\\frac{x}{y}$ and $\\sum_{i=1}^{n}$ work", &["$\\frac{x}{y}$", "$\\sum_{i=1}^{n}$"]),
            ("$$\\frac{a}{b}$$", &["$$\\frac{a}{b}$$"]),
            (
                "$$\n\\int_{-\\infty}^{\\infty} e^{-x^2} \\, dx = \\sqrt{\\pi}\n$$",
                &["e^{-x^2}", "\\sqrt{\\pi}"],
            ),
            ("{/* a note */}\n\n<Component />\n", &["{/* a note */}"]),
            ("{/* first line\n    second line */}\n", &["second line */}"]),
            ("Use {config} in the template.\n", &["\\{config\\}"]),
        ];
    for (input, expected) in cases {
        let result = sanitize_for_mdx(input);
        for needle in *expected {
            assert!(
                result.contains(needle),
                "{input:?} -> {result:?} lacks {needle:?}"
            );
        }
    }
}

#[test]
fn exact_outputs_for_inline_code_and_comments() {
    assert_eq!(
        sanitize_for_mdx("Route is `/{repo}` here."),
        "Route is `/{repo}` here."
    );
    assert_eq!(
        sanitize_for_mdx("A `{kept}` and a {escaped} one."),
        "A `{kept}` and a \\{escaped\\} one."
    );
    let comment = sanitize_for_mdx("{/* a note */}\n\n<Component />\n");
    assert!(!comment.contains("*/\\}"));
    let multiline = sanitize_for_mdx("{/* first line\n    second line */}\n");
    assert!(!multiline.contains("\\}"));
}

#[test]
fn html_and_jsx_lines_pass_through_unescaped() {
    let input = "<Callout title=\"Tip\">\n  Keep {this}.\n</Callout>\n\n<Swot\n  title=\"x\"\n  strengths={[\"a\"]}\n/>\n\nProse {b}.";
    let result = sanitize_for_mdx(input);
    assert!(result.contains("  Keep \\{this\\}."));
    assert!(result.contains("  strengths={[\"a\"]}"));
    assert!(result.contains("Prose \\{b\\}."));
    assert_eq!(
        sanitize_for_mdx("<div class=\"x\">a</div> and <span CLASS=\"y\">"),
        "<div className=\"x\">a</div> and <span className=\"y\">"
    );
}

#[test]
fn drops_unsupported_html_rst_directives_and_parent_images() {
    let result = sanitize_for_mdx(
            "Before\n<iframe src=\"x\"></iframe>\n<SCRIPT>alert(1)</script>\n<video src=\"v\" />\n<script>unclosed\n```{eval-rst}\n.. note:: x\n```\n![up](../img.png) ![here](./img.png)\nAfter",
        );
    assert_eq!(
        result,
        "Before\n\n\n\n<script>unclosed\n\n ![here](./img.png)\nAfter"
    );
    // A self-closing element with a stray closer later: only the tag goes,
    // not everything through the closer.
    assert_eq!(
        sanitize_for_mdx("<video src=\"v\" />\nkeep me\n</video>"),
        "\nkeep me\n</video>"
    );
}

#[test]
fn md_links_are_rewritten_outside_fences_only() {
    let result = sanitize_for_mdx("[x](./guide.md) [y](a.md#s)\n\n```md\n[z](./guide.md)\n```\n");
    assert_eq!(
        result,
        "[x](./guide) [y](a.md#s)\n\n```md\n[z](./guide.md)\n```\n"
    );
}

#[test]
fn mermaid_fences_become_a_component_and_nested_ones_stay_literal() {
    let result = convert_mermaid_blocks(
            "Intro\n\n```mermaid\nflowchart LR\n    A[\"x `y` ${z}\"] --> B\\n\n```\n\n````md\n```mermaid\nnested\n```\n````\n",
        );
    assert_eq!(
            result,
            "Intro\n\n<Mermaid chart={`flowchart LR\n    A[\"x \\`y\\` \\${z}\"] --> B\\\\n`} />\n\n````md\n```mermaid\nnested\n```\n````\n"
        );
    assert_eq!(convert_mermaid_blocks("```mermaid\n"), "");
}

#[test]
fn markdown_to_mdx_wraps_frontmatter_and_body() {
    let mut page = parse_markdown("# Hello\n\nSome content here.").unwrap();
    page.frontmatter.insert(
        "description".into(),
        serde_yaml_ng::Value::String("A greeting page.".into()),
    );
    assert_eq!(
        markdown_to_mdx(&page),
        "---\ndescription: A greeting page.\ntitle: Hello\n---\n\n# Hello\n\nSome content here.\n"
    );
    let highlight = parse_markdown(
            "# Example\n\n```python {2,4-6}\nimport os\nimport sys\nfrom pathlib import Path\ndef main():\n    print(\"hello\")\n    return 0\n```",
        )
        .unwrap();
    assert!(markdown_to_mdx(&highlight).contains("```python {2,4-6}"));
    let bare = MarkdownPage {
        content: "Just {text}".into(),
        ..MarkdownPage::default()
    };
    assert_eq!(markdown_to_mdx(&bare), "\nJust \\{text\\}\n");
}
