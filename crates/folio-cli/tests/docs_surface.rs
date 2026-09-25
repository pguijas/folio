//! Docs guides describe the runtime, first run, unavailable language profiles
//! and the failures of the binary that ships.

mod common;

const INSTALL_URL: &str = "https://pguijas.github.io/folio/install.sh";

fn read(rel: &str) -> String {
    common::read(&common::repo().join(rel))
}

#[test]
fn readiness_docs_cover_runtime_requirements() {
    let readme = read("README.md");
    let quickstart = read("docs/guide/quickstart.md");
    let installation = read("docs/guide/installation.md");

    for content in [&readme, &quickstart] {
        assert!(content.contains("Node.js 20.19+"));
        assert!(content.contains("pnpm 10"));
    }
    // The landing-tier pages present Folio as one native binary; the runtime
    // facts live where a reader looks for them.
    assert!(readme.contains("native Rust binary"));
    assert!(readme.contains("Nextra/Next.js template"));
    assert!(quickstart.contains("does not need Python"));
    assert!(installation.contains("one native binary"));
    assert!(!installation.contains("Python 3.10"));
}

#[test]
fn quickstart_uses_the_installed_cli_for_the_complete_first_run() {
    let quickstart = read("docs/guide/quickstart.md");
    assert!(!quickstart.contains("<TerminalSession"));
    for command in ["folio init", "folio serve", "folio build --clean"] {
        assert!(quickstart.contains(command), "quickstart runs `{command}`");
    }
    assert!(quickstart.contains(&format!("curl -LsSf {INSTALL_URL} | sh")));
    assert!(!quickstart.contains("uv run folio"));
}

#[test]
fn not_available_notices_open_the_pages_they_gate() {
    for rel in ["docs/guide/api-reference.md", "docs/guide/languages.md"] {
        let content = read(rel);
        let heading = content
            .find("\n# ")
            .unwrap_or_else(|| panic!("{rel} has an H1"));
        // The frontmatter description may carry the phrase too; the body is
        // what a reader sees, so look after the H1.
        let notice = content[heading..]
            .find("Not available in this release")
            .unwrap_or_else(|| panic!("{rel} carries the notice"));
        // A Callout right under the H1, not a footnote.
        assert!(notice < 400, "{rel}: the notice is not at the top");
    }
    // Folio's own API reference is not published in this release.
    assert!(!read("docs.yaml").contains("\n  python:\n    paths:"));
}

#[test]
fn troubleshooting_quotes_what_the_binary_prints_and_flags_it_has() {
    // The page is a lookup table of messages: a reworded message or a renamed
    // flag has to reword the page with it.
    let page = read("docs/guide/troubleshooting.md");

    let empty = tempfile::tempdir().unwrap();
    let missing = common::folio(empty.path(), &["build"], &[]);
    let printed = format!("{}{}", missing.stdout, missing.diagnostics());
    assert!(
        printed.contains("Config file not found"),
        "a project without docs.yaml still fails with the message the page \
         quotes: {printed}"
    );
    assert!(page.contains("`Config file not found`"));
    assert!(page.contains("`Environment check failed`"));
    assert!(page.contains("`Unknown config keys in docs.yaml`"));
    assert!(page.contains(".build/.folio-build.log"));

    for (command, flags) in [
        ("build", ["--clean", "--verbose", "--config"]),
        ("serve", ["--clean", "--kill-existing", "--port"]),
    ] {
        let run = common::folio(&common::repo(), &[command, "--help"], &[]);
        let help = &run.ok().stdout;
        for flag in flags {
            assert!(help.contains(flag), "`folio {command} --help` lists {flag}");
            assert!(
                page.contains(flag),
                "the page tells someone to run {flag} for `folio {command}`"
            );
        }
    }
}
