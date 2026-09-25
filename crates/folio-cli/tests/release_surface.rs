//! The distribution contract: the installer, published installation
//! instructions, release archives, canonical links and package version.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

const INSTALL_URL: &str = "https://pguijas.github.io/folio/install.sh";
const KNOBS: [&str; 4] = [
    "FOLIO_VERSION",
    "FOLIO_INSTALL_DIR",
    "FOLIO_REPO",
    "FOLIO_DOWNLOAD_URL",
];

fn repo() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root")
}

fn read(rel: &str) -> String {
    let path = repo().join(rel);
    fs::read_to_string(&path).unwrap_or_else(|err| panic!("{}: {err}", path.display()))
}

fn markdown_files(dir: &Path, out: &mut Vec<PathBuf>) {
    for entry in fs::read_dir(dir).expect("readable docs directory") {
        let path = entry.expect("directory entry").path();
        if path.is_dir() {
            markdown_files(&path, out);
        } else if path.extension().is_some_and(|ext| ext == "md") {
            out.push(path);
        }
    }
}

#[test]
fn installer_is_valid_shell_and_documents_its_knobs() {
    let path = repo().join("install.sh");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mode = fs::metadata(&path)
            .expect("install.sh")
            .permissions()
            .mode();
        assert!(mode & 0o111 != 0, "install.sh must be executable");
    }
    let status = Command::new("sh")
        .arg("-n")
        .arg(&path)
        .status()
        .expect("sh is available");
    assert!(status.success(), "sh -n install.sh");

    let installer = read("install.sh");
    for knob in KNOBS {
        assert!(installer.contains(knob), "install.sh documents {knob}");
    }
    assert!(installer.contains("releases/latest/download/"));
    assert!(installer.contains("Node.js 20.19+"));
    // The binary has no runtime: no uv bootstrap, no package install.
    assert!(!installer.contains("astral.sh/uv"));
    assert!(!installer.contains("uv tool install"));
}

#[test]
fn the_one_liner_is_the_only_install() {
    let one_liner = format!("curl -LsSf {INSTALL_URL} | sh");
    assert!(read("docs.yaml").contains(&format!("- \"{one_liner}\"")));

    for rel in [
        "README.md",
        "docs/guide/installation.md",
        "docs/guide/quickstart.md",
    ] {
        assert!(
            read(rel).contains(&one_liner),
            "{rel} installs with the one-liner"
        );
    }
    for rel in [
        "README.md",
        "docs/guide/index.md",
        "docs/guide/installation.md",
        "docs/guide/quickstart.md",
        "docs/guide/deployment/index.md",
        "docs/guide/deployment/static-hosts.md",
        "docs/guide/deployment/ci-cd.md",
    ] {
        let content = read(rel);
        for stale in [
            "uv tool install folio-docs",
            "uv add folio-docs",
            "pip install folio-docs",
        ] {
            assert!(!content.contains(stale), "{rel} still says `{stale}`");
        }
    }

    let installation = read("docs/guide/installation.md");
    assert!(installation.contains(&format!("curl -LsSf {INSTALL_URL} | less")));
    for knob in KNOBS {
        assert!(
            installation.contains(&format!("`{knob}`")),
            "installation documents {knob}"
        );
    }
    assert!(installation.contains("corepack prepare pnpm@10 --activate"));
    assert!(installation.contains("`folio build` and `folio serve`"));
}

#[test]
fn published_github_links_point_at_the_canonical_repo() {
    const PREFIX: &str = "https://github.com/pguijas/";
    let mut published = vec![repo().join("docs.yaml"), repo().join("README.md")];
    markdown_files(&repo().join("docs"), &mut published);

    let mut offenders = Vec::new();
    for path in published {
        let text = fs::read_to_string(&path).expect("published file");
        for (number, line) in text.lines().enumerate() {
            let mut rest = line;
            while let Some(at) = rest.find(PREFIX) {
                let after = &rest[at + PREFIX.len()..];
                let repo_name: String = after
                    .chars()
                    .take_while(|c| !c.is_whitespace() && !matches!(c, '/' | ')' | '"' | '\''))
                    .collect();
                if repo_name != "folio" {
                    offenders.push(format!(
                        "{}:{}: {PREFIX}{repo_name}",
                        path.strip_prefix(repo()).unwrap_or(&path).display(),
                        number + 1
                    ));
                }
                rest = after;
            }
        }
    }
    assert!(
        offenders.is_empty(),
        "published links must use {PREFIX}folio: {}",
        offenders.join("; ")
    );
}

#[test]
fn the_release_workflow_builds_what_the_installer_downloads() {
    let workflow = read(".github/workflows/release.yml");
    let installer = read("install.sh");

    // A release is a `v*` tag; the build alone also runs on pull requests that
    // touch the workflow or the installer.
    assert!(workflow.contains("tags: [\"v*\"]"));
    assert!(workflow.contains("paths: [\".github/workflows/release.yml\", \"install.sh\"]"));

    // The five targets, named the way install.sh composes them from uname.
    for triple in [
        "x86_64-unknown-linux-gnu",
        "aarch64-unknown-linux-gnu",
        "x86_64-apple-darwin",
        "aarch64-apple-darwin",
    ] {
        assert!(
            workflow.contains(&format!("target: {triple}")),
            "release.yml builds {triple}"
        );
    }
    assert!(installer.contains("-unknown-linux-gnu") && installer.contains("-apple-darwin"));
    assert!(workflow.contains("target: x86_64-pc-windows-msvc"));
    assert!(installer.contains("folio-x86_64-pc-windows-msvc.zip"));

    // One archive per target, the binary at the archive root, the names the
    // installer downloads.
    assert!(workflow.contains("dist/folio-${{ matrix.target }}.tar.gz"));
    assert!(workflow.contains("dist/folio-${{ matrix.target }}.zip"));
    assert!(installer.contains("asset=\"folio-$triple.tar.gz\""));
    assert!(
        workflow.contains("sh install.sh"),
        "the workflow runs the installer against its own archive"
    );

    // install.sh resolves `releases/latest`, which never points at a prerelease.
    assert!(installer.contains("releases/latest/download/"));
    assert!(!workflow.contains("--prerelease"));
    assert!(workflow.contains("SHA256SUMS"));

    // The notes are the version's CHANGELOG.md entry, which must exist.
    assert!(workflow.contains("--notes-file notes.md") && !workflow.contains("--generate-notes"));
    let version = quoted_value(&read("Cargo.toml"), "[workspace.package]", "version");
    let changelog = read("CHANGELOG.md");
    assert!(
        changelog
            .lines()
            .any(|line| line.starts_with(&format!("## {version} "))),
        "CHANGELOG.md has an entry for {version}"
    );
}

fn quoted_value(text: &str, section: &str, key: &str) -> String {
    let body = &text[text
        .find(section)
        .unwrap_or_else(|| panic!("{section} present"))..];
    let line = body
        .lines()
        .skip(1)
        .find(|line| line.trim_start().starts_with(key))
        .unwrap_or_else(|| panic!("{key} under {section}"));
    line.split('"').nth(1).expect("quoted value").to_string()
}

#[test]
fn the_workspace_and_the_site_agree_on_the_version() {
    let cargo = quoted_value(&read("Cargo.toml"), "[workspace.package]", "version");
    let site = quoted_value(&read("docs.yaml"), "project:", "version:");
    assert_eq!(
        site, cargo,
        "docs.yaml spells project.version exactly as Cargo.toml does"
    );
}
