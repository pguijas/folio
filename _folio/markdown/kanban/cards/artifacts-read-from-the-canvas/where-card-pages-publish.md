# Where card pages publish

Written 2026-08-24, beside four prototypes of reading a card's artifacts from
the board canvas. The prototypes answer how a human reads a card's output
without leaving the board. This note answers the other half of the owner's
verdict, that card pages indexing into /docs is weird: where should the
compiled pages live, and which surfaces should carry them.

## Where a card page goes today

`collect_docs` (folio/plugins/kanban.py:402) hands every visible `.md`/`.mdx`
under `board/cards/<id>/` to the core pipeline, routed by `_card_page_route`
(kanban.py:800) under `_CARD_PAGE_ROOT = "kanban"` (kanban.py:105). From there
the page is an ordinary document: `_collect_plugin_docs` (folio/build.py:628)
parses it with the same parser as any `source.docs` file, and
`_reject_duplicate_doc_routes` (build.py:676) fails the build on a collision.
Six surfaces then pick it up, and each deserves its own verdict.

**Route.** `/docs/kanban/<id>/<stem>/`, full documentation chrome, linked from
the artifact tile by `_resolve_artifact_hrefs` (kanban.py:275). The address
itself is sound: a decision document with a stable URL is the point of
compiling at all. The weirdness lives in what surrounds it.

**Docs sidebar.** Listed, and this is the leak that prompted the verdict.
`_write_meta_pages` (build.py:795) feeds every document, plugin-contributed
included (merged at build.py:593), to the sidebar generator, and
`_generate_doc_meta` (folio/generator/sidebar.py:263) writes a `_meta.ts`
entry for each. The current build shows the result: a "Kanban" folder sits
between "Migrating from Sphinx" and "Source Code" (.build/content/_meta.ts),
holding a title-cased folder per card, "The Board Reads As A Tree"
(.build/content/kanban/_meta.ts). The sidebar is the documentation's table of
contents; board working papers have no place in its teaching order. Wrong
surface.

**Search.** Indexed. The Pagefind postbuild covers
`{index.html,docs/**/*.html}` (template/package.json:9): everything under
/docs and nothing else — the standalone /kanban board page is not indexed.
Right surface. Search is how a reader who does not know the board's layout
finds "swimlanes" in the comparison document; the canvas filter searches card
fields, not artifact bodies.

**Sitemap.** Listed. `template/app/sitemap.ts` walks `content/*.mdx` (lines
15-24) and emits each page at priority 0.6 plus its Markdown mirror at 0.3
(lines 41-48, 87-92). Right, or at worst harmless: the sitemap lists what is
published, and hiding a live page from crawlers would not make it less
published.

**llms.txt.** Present in both files: `generate_llms_txt` links every document
(folio/generator/llm_output.py:229) and `generate_llms_full_txt` embeds the
whole body (llm_output.py:269); both take the merged docs list (build.py:1096
and 1101). Right surface, and explicitly promised — the owning card's checked
criterion reads "a `.md` sibling renders as a page ... in the search index
and in `llms.txt`" (artifacts-live-beside-their-card.md:129).

**Markdown mirrors.** Written. `_write_page_markdown`
(folio/generator/site_builder.py:540) puts
`public/_folio/markdown/kanban/<id>/<stem>.md` beside every compiled page,
and the docs head declares it as a `text/markdown` alternate
(template/app/docs/[[...mdxPath]]/page.jsx:43-81). Right surface; this is the
copy an agent actually fetches.

The raw bundle at `/_folio/kanban/<id>/` (`_publish_card_assets`,
kanban.py:724) sits on none of these surfaces, which is correct for emitted
output.

So the problem is one surface out of six. Route, search, sitemap, llms output
and mirrors behave exactly as a published decision document should. The
sidebar listing is the part that presents board output as documentation.

## The options

**(a) Keep compiling under /docs; delist deliberately.** The sidebar
generator cannot currently tell a plugin document from an authored one:
`MarkdownResult` carries no origin, so `_generate_doc_meta` lists everything
it is given. Delisting means carrying an unlisted flag from `PluginDocument`
through `_collect_plugin_docs` into the meta generator and emitting
`{"display": "hidden"}` for the subtree. The generator already hides nested
index pages with exactly that value (sidebar.py:316); omission alone is not
enough, because Nextra lists content pages by default and `_meta.ts` only
orders and hides. Everything else stays. Per surface: sidebar out, search
keep, sitemap keep, llms.txt keep, mirrors keep.

**(b) Compile under the board's namespace, `/kanban/<id>/<stem>/`, in board
chrome.** This costs most of the machinery that makes the pages cheap.
There is no second content tree: `SiteBuilder._page_path`
(site_builder.py:527) roots every compiled page in `content/`, and the one
catch-all route serving that tree lives under the docs base, so board-chrome
pages need a second catch-all route and layout in the template. The
standalone view mechanism cannot carry them: `_write_view`
(folio/generator/extension_emitter.py:174) renders registered components
with JSON props into a single app route and has no MDX pipeline, so each
card page would become a component call holding pre-rendered HTML, a second
Markdown path beside the real one, nested under the already-emitted /kanban
view (kanban.py:394). Search silently empties, because the Pagefind glob
(template/package.json:9) covers docs/** only; the sitemap stops seeing them,
because sitemap.ts walks content/*.mdx; mirrors are written per content route
(site_builder.py:540); and link validation accepts non-docs routes only as
view routes (`_check_generated_links`, build.py:957), so a tree of board
pages is a new class of valid target. Five inherited surfaces rebuilt, to
change a breadcrumb and a frame that the page's remaining visitors barely
experience, since they arrive from a pasted link, a search hit, or an agent
fetch.

**(c) Stop compiling; the canvas renders from the raw bundle.** Delete or
gate `collect_docs` (kanban.py:402) and the page disappears together with its
search entry, sitemap line, llms.txt line, full-text section and mirror,
un-checking the owning card's shipped criterion
(artifacts-live-beside-their-card.md:129). Reading moves client-side: the
prototypes here read pre-rendered HTML out of `reader-data.js` precisely
because nothing in the browser parses Markdown, so the product would need a
runtime renderer or a build step that pre-renders into the bundle — which is
the compile step again, minus every surface it fed. A `doc:` artifact href
(kanban.py:275) reverts to the raw file under /_folio/kanban/, which the code
itself calls "an unstyled download of something the site already renders"
(kanban.py:234). And a deep link has nowhere durable to land except a
canvas-state URL that must boot the whole board app before a document is
readable.

## Recommendation

Option (a). Once the canvas is the human reading path, the compiled page has
three jobs left: be the durable address a link from outside lands on; be
findable, by Pagefind for people and by llms.txt and the mirror for agents;
and stay out of the way. Option (a) is the only one that serves all three.
Option (c) deletes the first two. Option (b) rebuilds five surfaces to
improve the third by a margin nobody arriving at the page will notice.

Concretely: card pages stay at `/docs/kanban/<id>/<stem>/` and keep search,
sitemap, llms output and Markdown mirrors; they leave the docs sidebar, which
was the weirdness. The canvas reader and the compiled page then divide the
work the way the board and the roadmap already do. The canvas is where a
card's output is read in context; the page is the address that output
answers to.
