//! Markdown body to MDX: mermaid fences to `<Mermaid>`, unsupported HTML and
//! RST directives dropped, `.md` links rewritten, bare braces escaped.

use regex::Regex;

use crate::escape::{code_fence_flags, escape_curly_outside_math};
use crate::frontmatter::render_frontmatter;
use crate::page::MarkdownPage;
use crate::re;

/// Turns top-level ```` ```mermaid ```` fences into `<Mermaid chart={`…`} />`.
/// A mermaid fence nested inside a 4+ tick fence stays literal.
pub fn convert_mermaid_blocks(content: &str) -> String {
    let mut out = Vec::new();
    let mut outer_fence: Option<usize> = None;
    let mut chart: Option<Vec<&str>> = None;
    for line in content.split('\n') {
        let stripped = line.trim_end();
        if stripped.starts_with("```") {
            let ticks = stripped.bytes().take_while(|&b| b == b'`').count();
            if let Some(outer) = outer_fence {
                if ticks >= outer && ticks == stripped.len() {
                    outer_fence = None;
                }
                out.push(line.to_string());
                continue;
            }
            if ticks >= 4 {
                outer_fence = Some(ticks);
                out.push(line.to_string());
                continue;
            }
            if let Some(lines) = chart.take() {
                let text = lines.join("\n");
                let escaped = text
                    .trim_end_matches('\n')
                    .replace('\\', "\\\\")
                    .replace('`', "\\`")
                    .replace("${", "\\${");
                out.push(format!("<Mermaid chart={{`{escaped}`}} />"));
                continue;
            }
            if stripped == "```mermaid" {
                chart = Some(Vec::new());
                continue;
            }
        }
        match chart.as_mut() {
            Some(lines) => lines.push(line),
            None => out.push(line.to_string()),
        }
    }
    out.join("\n")
}

const HTML_ELEMENTS: &str = "iframe|script|style|video|audio|object|embed";

/// Drops `<iframe>`, `<script>`, `<style>`, `<video>`, `<audio>`, `<object>`
/// and `<embed>` elements, self-closing or with their body; an unclosed one
/// stays as written.
fn strip_html_elements(content: &str) -> String {
    let open = re(&format!("(?i)<({HTML_ELEMENTS})[^>]*>"));
    let close = re(&format!("(?i)</({HTML_ELEMENTS})>"));
    let mut out = String::with_capacity(content.len());
    let mut pos = 0;
    while let Some(caps) = open.captures_at(content, pos) {
        let tag = caps.get(0).expect("whole match");
        let name = &caps[1];
        let end = if tag.as_str().ends_with("/>") {
            Some(tag.end())
        } else {
            close
                .captures_iter(&content[tag.end()..])
                .find(|c| c[1].eq_ignore_ascii_case(name))
                .map(|c| tag.end() + c.get(0).expect("whole match").end())
        };
        match end {
            Some(end) => {
                out.push_str(&content[pos..tag.start()]);
                pos = end;
            }
            None => {
                out.push_str(&content[pos..tag.start() + 1]);
                pos = tag.start() + 1;
            }
        }
    }
    out.push_str(&content[pos..]);
    out
}

/// The whole-body transformation authored Markdown gets before it becomes
/// MDX. Fenced code is never touched; `<`/`>` are never escaped (authors
/// write JSX); the `.md` link rewrite fires outside fences only.
pub fn sanitize_for_mdx(content: &str) -> String {
    let content = convert_mermaid_blocks(content);
    let content = re(r"!\[([^\]]*)\]\((\.\./[^)]+)\)").replace_all(&content, "");
    let content = strip_html_elements(&content);
    let content = re(r"```\{[^}]+\}\n[\s\S]*?```").replace_all(&content, "");

    let lines: Vec<&str> = content.split('\n').collect();
    let in_code = code_fence_flags(&lines);
    let md_link = re(r"\]\(([^)]+)\.md\)");
    let class_attr: Regex = re(r"(?i)(<[^>]*)\bclass=");
    let mut out = Vec::with_capacity(lines.len());
    let (mut in_math_block, mut in_html_tag) = (false, false);
    for (line, &in_code) in lines.iter().zip(&in_code) {
        if in_code {
            out.push(line.to_string());
            continue;
        }
        let mut line = md_link.replace_all(line, "]($1)").into_owned();
        if line.trim() == "$$" {
            in_math_block = !in_math_block;
        }
        if !in_math_block {
            let stripped = line.trim();
            let is_html_line = stripped.starts_with('<') || in_html_tag;
            if stripped.starts_with('<') && !stripped.ends_with('>') {
                in_html_tag = true;
            } else if in_html_tag && stripped.ends_with('>') {
                in_html_tag = false;
            }
            if !is_html_line {
                line = escape_curly_outside_math(&line);
            }
            line = class_attr.replace_all(&line, "${1}className=").into_owned();
        }
        out.push(line);
    }
    out.join("\n")
}

/// `[frontmatter]\n<sanitized body>\n`; a page without frontmatter starts
/// with a blank line.
pub fn markdown_to_mdx(page: &MarkdownPage) -> String {
    let frontmatter = if page.frontmatter.is_empty() {
        String::new()
    } else {
        render_frontmatter(&page.frontmatter)
    };
    format!("{frontmatter}\n{}\n", sanitize_for_mdx(&page.content))
}

#[cfg(test)]
#[path = "sanitize_tests.rs"]
mod tests;
