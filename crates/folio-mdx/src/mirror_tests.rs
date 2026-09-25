use super::*;

#[test]
fn strips_the_mdx_shell_and_keeps_prose() {
    let markdown = mdx_to_markdown(
            "---\ntitle: Guide\n---\nimport { Callout } from \"@/components/callout\"\n\n# Guide\n\n<Callout type=\"info\">\nUse this content.\n</Callout>\n\n<ParamTable args={[]} />\n",
        );
    assert_eq!(markdown, "# Guide\n\nUse this content.\n");
    let plain =
        mdx_to_markdown("---\ntitle: Getting Started\n---\n\n# Getting Started\n\nHello world.\n");
    assert_eq!(plain, "# Getting Started\n\nHello world.\n");
    assert_eq!(mdx_to_markdown(""), "\n");
    assert_eq!(mdx_to_markdown("---\ntitle: Source Code\n---\n\n<ApiReferenceIndex modules={[\n  {\n    \"name\": \"a\"\n  }\n]} />\n"), "- **a**\n");
}

#[test]
fn authored_mdx_imports_exports_and_components_go() {
    let markdown = mdx_to_markdown(
            "import { Callout } from 'nextra/components'\nexport const meta = {}\n\n# Guide\n\n<Callout type='info'>Read this.</Callout>\n\nPlain body.\n",
        );
    assert_eq!(markdown, "# Guide\n\nRead this.\n\nPlain body.\n");
}

#[test]
fn protects_indented_nested_and_inline_code() {
    let cases = [
        (
            "1. Render it:\n\n   ```html\n   <Page title=\"x\">body</Page>\n   ```\n",
            "<Page title=\"x\">body</Page>",
        ),
        (
            "> Example:\n>\n> ```html\n> <Card>text</Card>\n> ```\n",
            "<Card>text</Card>",
        ),
        (
            "````markdown\n```html\n<Note>hi</Note>\n```\n````\n",
            "<Note>hi</Note>",
        ),
        (
            "Tags in markdown (`<Callout>`, ``<Swot>``) work.\n",
            "(`<Callout>`, ``<Swot>``)",
        ),
        ("~~~jsx\n<Tabs>\n~~~\n", "<Tabs>"),
    ];
    for (content, kept) in cases {
        let markdown = mdx_to_markdown(content);
        assert!(markdown.contains(kept), "{content:?} -> {markdown:?}");
    }
    let unclosed = mdx_to_markdown("```js\n<Tabs>\nno closer\n\n<Other />\n");
    assert_eq!(unclosed, "```js\n\nno closer\n");
}

#[test]
fn restores_mermaid_source() {
    let markdown = mdx_to_markdown(
        "<Mermaid chart={`flowchart LR\n    A[\"x \\`y\\` \\${z}\"] --> B\\\\n`} />\n\nAfter.\n",
    );
    assert_eq!(
        markdown,
        "```mermaid\nflowchart LR\n    A[\"x `y` ${z}\"] --> B\\\\n\n```\n\nAfter.\n"
    );
    assert_eq!(mdx_to_markdown("<Mermaid chart={`open`} >\n"), "\n");
}

#[test]
fn simple_components_leave_a_text_trace() {
    let cases = [
        (
            "<FeatureCard title=\"A\" description=\"D\" href=\"/x\" />",
            "- **[A](/x)**: D\n",
        ),
        (
            "<FeatureCard\n  title=\"A\"\n  href=\"/x\"\n/>",
            "- **[A](/x)**\n",
        ),
        (
            "<CommandCard command=\"folio build\" description=\"Build.\" />",
            "- **folio build**: Build.\n",
        ),
        ("<FeatureCard description=\"Only text\" />", "- Only text\n"),
        ("<FeatureCard icon=\"api\" />", "\n"),
        (
            "<FeatureCard title={dynamic} description='It\\'s' />",
            "- It\\\n",
        ),
        (
            "<AccordionItem title=\"Why?\">\nBecause.\n</AccordionItem>",
            "### Why?\n\nBecause.\n",
        ),
        ("<Step title=\"One\">go</Step>", "### One\n\ngo\n"),
        ("<TabItem label=\"pnpm\">run</TabItem>", "### pnpm\n\nrun\n"),
        (
            "<Callout title=\"Tip\">\n  Keep it short.\n</Callout>",
            "**Tip**\n\n  Keep it short.\n",
        ),
        (
            "<PullQuote kicker=\"Aside\">text</PullQuote>",
            "**Aside**\n\ntext\n",
        ),
        (
            "<PreviewCode title=\"Demo\">x</PreviewCode>",
            "**Demo**\n\nx\n",
        ),
        ("<Callout type=\"info\">no label</Callout>", "no label\n"),
        (
            "<Swot\n  title=\"x\"\n  strengths={[\n    \"a }> b\",\n  ]}\n/>\ntail",
            "tail\n",
        ),
        (
            "<ClassOverview name=\"Foo\" bases={[\"Config\"]} decorators={[]} />",
            "**class Foo(Config)**\n",
        ),
        (
            "a <- b <= c <div class=\"x\">html</div> <br/>",
            "a <- b <= c <div class=\"x\">html</div> <br/>\n",
        ),
        (
            "<Unterminated title=\"x\"\nrest",
            "<Unterminated title=\"x\"\nrest\n",
        ),
    ];
    for (input, expected) in cases {
        assert_eq!(mdx_to_markdown(input), expected, "{input:?}");
    }
}

#[test]
fn whitespace_is_normalised() {
    assert_eq!(mdx_to_markdown("a\n  \t\n\n\n\nb\n\n\n"), "a\n\nb\n");
}

#[test]
fn the_api_components_become_markdown() {
    let page = concat!(
        "<span id=\"store\" />\n\n<ClassOverview name=\"Store\" bases={[{\"name\": \"Base\", \"href\": \"/docs/a#base\"}, {\"name\": \"dict[str, int]\"}]} decorators={[\"dataclass\"]} /> <SourceLink href=\"x\" />\n\n",
        "<ParamTable args={[\n  {\n    \"name\": \"key\",\n    \"type\": \"str | None\",\n    \"default\": \"None\",\n    \"description\": \"The `key`, or\\nnothing.\",\n    \"href\": \"/docs/a#key\"\n  },\n  {\n    \"name\": \"*rest\",\n    \"type\": \"Any\",\n    \"default\": \"\",\n    \"description\": \"\"\n  }\n]} />\n",
    );
    assert_eq!(
        mdx_to_markdown(page),
        concat!(
            "`@dataclass`\n\n**class Store([Base](/docs/a#base), dict[str, int])**\n\n",
            "| Parameter | Type | Default | Description |\n| --- | --- | --- | --- |\n",
            "| `key` | [`str \\| None`](/docs/a#key) | `None` | The `key`, or nothing. |\n",
            "| `*rest` | `Any` |  |  |\n",
        )
    );
    // A hand-written JS literal is not JSON: the tag goes as before.
    assert_eq!(mdx_to_markdown("<ParamTable args={[{name: 'x'}]} />"), "\n");
}

#[test]
fn headings_lose_their_id_and_escapes_are_undone_outside_code() {
    assert_eq!(
        mdx_to_markdown(
            "# pkg <SourceLink href=\"x\" />\n\n### `add` <SourceLink href=\"x\" /> [#add]\n\n## Plain [#plain]\n\nA \\{dict\\} of &lt;T&gt; and `\\{kept\\} &lt;`.\n"
        ),
        "# pkg\n\n### `add`\n\n## Plain\n\nA {dict} of <T> and `\\{kept\\} &lt;`.\n"
    );
}
