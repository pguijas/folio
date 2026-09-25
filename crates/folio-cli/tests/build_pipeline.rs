//! `folio build` end to end on `docs/examples/generated-site`
//! with the frontend runtime stubbed (`FOLIO_FRONTEND_RUNTIME=noop`): the
//! transcript rows, the generated pages against the golden fixture, the
//! manifest, the contract, the sidebar files, warm and `--clean` rebuilds,
//! LLM files, `public:` files and the failure lines. One ignored test runs
//! the real export.

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use std::process::Command;

use serde_json::Value;

mod common;

use common::{example_project, read, repo, Run};

fn folio(cwd: &Path, args: &[&str]) -> Run {
    common::folio(cwd, args, &[])
}

/// The pages a build must write, checked in with the crate that generates
/// them; `folio-docs` compares them page by page, this suite through the CLI.
fn golden() -> std::path::PathBuf {
    repo().join("crates/folio-docs/tests/fixtures/generated_site")
}

fn json(path: &Path) -> Value {
    serde_json::from_str(&read(path)).unwrap_or_else(|e| panic!("{}: {e}", path.display()))
}

/// Every file under `root` as `(relative posix path, bytes)`.
fn tree(root: &Path) -> Vec<(String, Vec<u8>)> {
    fn walk(dir: &Path, root: &Path, out: &mut Vec<(String, Vec<u8>)>) {
        let mut entries: Vec<_> = fs::read_dir(dir).unwrap().flatten().collect();
        entries.sort_by_key(|e| e.path());
        for entry in entries {
            let path = entry.path();
            if path.is_dir() {
                walk(&path, root, out);
            } else {
                let rel = path
                    .strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/");
                out.push((rel, fs::read(&path).unwrap()));
            }
        }
    }
    let mut out = Vec::new();
    if root.exists() {
        walk(root, root, &mut out);
    }
    out
}

fn contract_without_timestamp(build: &Path) -> Value {
    let mut contract = json(&build.join("public/_folio/contract.json"));
    contract.as_object_mut().unwrap().remove("generatedAt");
    contract
}

const EXPECTED_ROUTES: [&str; 6] = [
    "/docs/",
    "/docs/api-reference/",
    "/docs/api-reference/example_package/",
    "/docs/api-reference/example_package/arithmetic/",
    "/docs/cli/",
    "/docs/components/",
];

#[test]
fn build_writes_the_golden_pages_and_prints_the_transcript() {
    let (_dir, project) = example_project();
    let build = project.join(".build");
    let run = folio(&project, &["build"]);
    run.ok();
    assert!(run.diagnostics().is_empty(), "{}", run.stderr);

    // The banner opens the transcript: blank, six art lines with the version, blank.
    let lines: Vec<&str> = run.stdout.lines().collect();
    assert_eq!(lines[0], "");
    assert!(lines[1].contains("████████╗ ██████╗ ██╗"));
    assert!(lines[6].ends_with(&format!("╚═════╝  v{}", env!("CARGO_PKG_VERSION"))));
    assert_eq!(lines[7], "");
    assert!(!run.stdout.contains('⚡'));

    let rows = run.rows();
    assert_eq!(rows[0], "✓ Sources      › 2 modules, 3 doc pages");
    assert_eq!(rows[1], "✓ Template     › .build/ workspace ready");
    assert_eq!(rows[2], "✓ Pages        › 5 pages");
    assert_eq!(rows[3], "✓ Links        › valid");
    assert_eq!(
        rows[4],
        "✓ Dependencies › up to date, the lockfile has not moved"
    );
    assert_eq!(rows[5], "✓ Export       › Site export completed");
    assert!(
        rows[6].starts_with("✓ Done         › 5 pages in ") && rows[6].ends_with('s'),
        "{}",
        rows[6]
    );
    assert_eq!(rows[7], "✓ Site ready   › _site/");
    assert_eq!(rows.len(), 8);
    for forbidden in [
        "Build complete",
        "Static site ready at",
        "Ctrl+O",
        "01  Sources",
        "  ✓ Sources",
        "Previews",
        "Build output",
    ] {
        assert!(
            !run.stdout.contains(forbidden),
            "{forbidden} in\n{}",
            run.stdout
        );
    }

    // Generated pages equal the golden fixture byte for byte.
    let golden = golden().join("api-reference");
    for rel in [
        "index.mdx",
        "example_package.mdx",
        "example_package/arithmetic.mdx",
    ] {
        assert_eq!(
            read(&build.join("content/api-reference").join(rel)),
            read(&golden.join(rel)),
            "{rel}"
        );
    }
    let index = read(&build.join("content/index.mdx"));
    assert!(index.starts_with("---\n"));
    assert!(index.contains("title: Example docs"));
    assert!(index.contains("\n# Example docs\n"));
    let cli = read(&build.join("content/cli.mdx"));
    assert!(cli.contains("description: 'Run the local preview server while editing:'"));
    assert!(cli.contains("title: CLI reference"));
    let components = read(&build.join("content/components.mdx"));
    assert!(components.contains("<Callout title=\"Tip\">"));
    assert_eq!(
        read(&build.join("public/_folio/markdown/components.md")),
        "# Components\n\nUse small MDX components when prose needs a clearer shape.\n\n**Tip**\n\n  Keep examples short. The preview should support the explanation, not replace the documentation.\n\n```python\nfrom example_package import add\n\nadd(2, 3)\n```\n"
    );
    for rel in [
        "index.md",
        "cli.md",
        "components.md",
        "api-reference/index.md",
        "api-reference/example_package.md",
        "api-reference/example_package/arithmetic.md",
    ] {
        assert!(
            build.join("public/_folio/markdown").join(rel).is_file(),
            "{rel}"
        );
    }

    // Sidebar metadata: the root and the api-reference tree.
    let root_meta = read(&build.join("content/_meta.ts"));
    assert!(root_meta.contains("api-reference"), "{root_meta}");
    assert!(build.join("content/api-reference/_meta.ts").is_file());
    assert!(build.join("lib/folio-mdx-contract.ts").is_file());
    assert!(build.join("lib/search-index.ts").is_file());

    // The authoring contract: routes, config keys without plugins, envelope.
    let contract = json(&build.join("public/_folio/contract.json"));
    let routes: Vec<&str> = contract["routes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap())
        .collect();
    assert_eq!(routes, EXPECTED_ROUTES);
    let keys: Vec<&str> = contract["configKeys"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap())
        .collect();
    assert!(!keys.contains(&"plugins"));
    assert!(keys.contains(&"landing") && keys.contains(&"public") && keys.contains(&"project"));
    assert_eq!(contract["folioVersion"], env!("CARGO_PKG_VERSION"));
    let stamp = contract["generatedAt"].as_str().unwrap();
    assert_eq!(stamp.len(), 20);
    assert!(
        stamp.ends_with('Z') && stamp.as_bytes()[10] == b'T',
        "{stamp}"
    );

    // The LLM files are off in the example: nothing written.
    let site = project.join("_site");
    assert!(!site.join("llms.txt").exists() && !site.join("llms-full.txt").exists());
    assert!(
        site.is_dir(),
        "the noop export still creates the output dir"
    );

    // The manifest: build context, then the sources in docs-then-modules order.
    let manifest = json(&build.join(".folio-manifest.json"));
    let keys: Vec<&String> = manifest.as_object().unwrap().keys().collect();
    assert_eq!(keys, ["build", "sources"]);
    let ctx = manifest["build"].as_object().unwrap();
    assert_eq!(
        ctx.keys().collect::<Vec<_>>(),
        [
            "config",
            "template",
            "theme_package",
            "docs_route_base",
            "generator",
            "source_ref",
            "experimental_features"
        ]
    );
    assert_eq!(ctx["config"].as_str().unwrap().len(), 64);
    assert_eq!(ctx["generator"].as_str().unwrap().len(), 64);
    assert_eq!(ctx["docs_route_base"], "/docs");
    assert_eq!(ctx["source_ref"], "main");
    assert_eq!(ctx["experimental_features"], "disabled");
    assert_eq!(ctx["theme_package"], "");
    let sources = manifest["sources"].as_object().unwrap();
    let source_keys: Vec<&String> = sources.keys().collect();
    assert_eq!(source_keys.len(), 5);
    assert!(source_keys
        .iter()
        .all(|k| k.starts_with(project.to_str().unwrap())));
    assert!(source_keys[0].ends_with(".md") && source_keys[3].ends_with(".py"));
    let doc = &sources[source_keys[0]];
    assert_eq!(
        doc.as_object().unwrap().keys().collect::<Vec<_>>(),
        ["hash", "route", "assets"]
    );
    assert_eq!(doc["assets"], serde_json::json!([]));
    let module = &sources[&format!("{}/src/example_package/arithmetic.py", project.display())];
    assert_eq!(
        module.as_object().unwrap().keys().collect::<Vec<_>>(),
        ["hash", "route", "symbols", "language"]
    );
    assert_eq!(module["route"], "api-reference/example_package/arithmetic");
    assert_eq!(module["language"], "python");
    assert_eq!(module["symbols"].as_str().unwrap().len(), 64);
    let text = read(&build.join(".folio-manifest.json"));
    assert!(text.starts_with("{\n  \"build\": {\n    \"config\": \"") && text.ends_with('}'));

    // A warm build skips every page, keeps the routes and changes nothing
    // but the manifest's identity.
    let before = tree(&build.join("content"));
    let before_public = tree(&build.join("public"));
    let before_manifest = read(&build.join(".folio-manifest.json"));
    let warm = folio(&project, &["build"]);
    warm.ok();
    let rows = warm.rows();
    assert_eq!(rows[2], "✓ Pages        › 5 pages, 5 skipped pages");
    assert_eq!(rows[5], "✓ Export       › Site export completed");
    assert_eq!(tree(&build.join("content")), before);
    assert_eq!(
        tree(&build.join("public")),
        before_public,
        "generatedAt must not advance"
    );
    assert_eq!(read(&build.join(".folio-manifest.json")), before_manifest);
    let routes = json(&build.join("public/_folio/contract.json"))["routes"].clone();
    assert_eq!(routes.as_array().unwrap().len(), EXPECTED_ROUTES.len());

    // A verbose warm build names the skipped pages.
    let verbose = folio(&project, &["build", "--verbose"]);
    verbose.ok();
    assert!(verbose.stdout.contains("  Skipped 5 unchanged page(s)"));
    assert!(verbose.stdout.contains(&format!(
        "  Scanning {}/src/example_package",
        project.display()
    )));
    assert!(verbose
        .stdout
        .contains(&format!("  Scanning {}/docs", project.display())));
    assert!(!verbose.stdout.contains("Writing page:"));

    // --clean regenerates everything and two clean builds differ only in
    // the contract's generatedAt.
    let clean = folio(&project, &["build", "--clean", "-v"]);
    clean.ok();
    assert_eq!(clean.rows()[2], "✓ Pages        › 5 pages");
    assert!(clean
        .stdout
        .contains("  Writing page: api-reference/example_package/arithmetic"));
    assert!(clean.stdout.contains("  Writing page: cli"));
    assert!(!clean.stdout.contains("Skipped"));
    assert_eq!(tree(&build.join("content")), before);
    let first_contract = contract_without_timestamp(&build);
    let first_manifest = read(&build.join(".folio-manifest.json"));
    folio(&project, &["build", "--clean"]).ok();
    assert_eq!(tree(&build.join("content")), before);
    assert_eq!(contract_without_timestamp(&build), first_contract);
    assert_eq!(read(&build.join(".folio-manifest.json")), first_manifest);

    // An edited generator fingerprint invalidates otherwise unchanged pages.
    let mut manifest = json(&build.join(".folio-manifest.json"));
    manifest["build"]["generator"] = Value::String("stale".into());
    fs::write(
        build.join(".folio-manifest.json"),
        serde_json::to_string_pretty(&manifest).unwrap(),
    )
    .unwrap();
    let regenerated = folio(&project, &["build"]);
    regenerated.ok();
    assert_eq!(regenerated.rows()[2], "✓ Pages        › 5 pages");

    // An incomplete `build` object counts as a changed context.
    let mut manifest = json(&build.join(".folio-manifest.json"));
    manifest["build"] = serde_json::json!({});
    fs::write(
        build.join(".folio-manifest.json"),
        serde_json::to_string_pretty(&manifest).unwrap(),
    )
    .unwrap();
    let incomplete = folio(&project, &["build"]);
    incomplete.ok();
    assert_eq!(incomplete.rows()[2], "✓ Pages        › 5 pages");

    // A matching manifest with a page missing on disk regenerates that page.
    fs::remove_file(build.join("content/cli.mdx")).unwrap();
    let repaired = folio(&project, &["build"]);
    repaired.ok();
    assert_eq!(
        repaired.rows()[2],
        "✓ Pages        › 5 pages, 4 skipped pages"
    );
    assert!(build.join("content/cli.mdx").is_file());
}

#[test]
fn a_build_traces_its_writes_and_a_warm_build_writes_nothing() {
    let (_dir, project) = example_project();
    let trace = project.join("trace.jsonl");
    let env = [("FOLIO_TRACE", trace.to_str().unwrap())];
    common::folio(&project, &["build"], &env).ok();
    let lines: Vec<Value> = read(&trace)
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert!(!lines.is_empty());
    for line in &lines {
        let keys: Vec<&String> = line.as_object().unwrap().keys().take(4).collect();
        assert_eq!(keys, ["event", "t_ns", "wall_ms", "batch"], "{line}");
        assert_eq!(line["batch"], 0, "a build runs outside any batch: {line}");
        assert!(line["t_ns"].is_u64() && line["wall_ms"].is_f64(), "{line}");
    }
    let writes: Vec<&Value> = lines
        .iter()
        .filter(|l| l["event"] == "file_write")
        .collect();
    assert!(writes.iter().any(|w| {
        w["path"]
            .as_str()
            .unwrap()
            .ends_with("content/api-reference/example_package/arithmetic.mdx")
            && w["bytes"].as_u64().unwrap() > 0
    }));
    assert!(writes.iter().any(|w| w["path"]
        .as_str()
        .unwrap()
        .ends_with(".folio-manifest.json")));
    // Write-if-changed: a warm build rewrites no page, mirror, contract or
    // manifest (the template copy alone re-stamps `lib/search-index.ts`).
    common::folio(&project, &["build"], &env).ok();
    let warm: Vec<Value> = read(&trace)
        .lines()
        .skip(lines.len())
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    let rewritten: Vec<&str> = warm
        .iter()
        .filter(|l| l["event"] == "file_write")
        .map(|l| l["path"].as_str().unwrap())
        .filter(|p| {
            p.contains("/content/") || p.contains("/public/") || p.ends_with(".folio-manifest.json")
        })
        .collect();
    assert!(rewritten.is_empty(), "a warm build rewrote {rewritten:?}");
    // An unopenable trace path is one warning; the build still runs.
    let bad = project.join("docs.yaml").join("trace.jsonl");
    let run = common::folio(
        &project,
        &["build"],
        &[("FOLIO_TRACE", bad.to_str().unwrap())],
    );
    run.ok();
    let trace_warning = run.diagnostics();
    assert!(
        trace_warning.contains(&format!("FOLIO_TRACE: cannot open {}: ", bad.display()))
            && trace_warning.contains("; tracing disabled"),
        "{trace_warning}"
    );
}

#[test]
fn llm_files_public_files_and_warnings() {
    let (_dir, project) = example_project();
    let build = project.join(".build");
    let config = read(&project.join("docs.yaml"))
        .replace("generate_llms_txt: false", "generate_llms_txt: true")
        .replace("generate_llms_full_txt: false", "generate_llms_full_txt: true")
        + "\npublic:\n  - \"docs/cli.md\"\n  - \"src/example_package/__init__.py\"\nversions:\n  - label: v1\nplugins:\n  - \"./x.py\"\nbogus: 1\n";
    fs::write(project.join("docs.yaml"), config).unwrap();

    let run = folio(&project, &["build"]);
    run.ok();
    let golden = golden();
    let site = project.join("_site");
    assert_eq!(read(&site.join("llms.txt")), read(&golden.join("llms.txt")));
    assert_eq!(
        read(&site.join("llms-full.txt")),
        read(&golden.join("llms-full.txt"))
    );
    assert_eq!(
        run.rows()[5],
        "✓ Export       › Site export completed, llms.txt, llms-full.txt"
    );

    // public: files land at the public root; the config warnings print once.
    assert_eq!(
        read(&build.join("public/cli.md")),
        read(&project.join("docs/cli.md"))
    );
    assert!(build.join("public/__init__.py").is_file());
    assert!(run
        .stdout
        .contains("warning: Unknown config keys in docs.yaml: bogus"));
    assert!(run.stdout.contains(
        "warning: project plugins are not available in this release; the plugins key is ignored"
    ));
    assert_eq!(
        run.stdout.matches("warning: Unknown config keys").count(),
        1
    );
    // versions: is gated, so no version note and an empty selector.
    assert!(!run.stdout.contains("Current version only"));

    // A missing image warns during Pages; a broken link is a warning row.
    fs::write(
        project.join("docs/missing.md"),
        "# Missing\n\n![shot](shot.png)\n\nSee [nowhere](./nowhere).\n",
    )
    .unwrap();
    let warm = folio(&project, &["build"]);
    warm.ok();
    assert!(warm
        .stdout
        .contains("warning: missing: image not found: shot.png"));
    let rows = warm.rows();
    assert_eq!(rows[0], "✓ Sources      › 2 modules, 4 doc pages");
    assert_eq!(rows[2], "✓ Pages        › 6 pages, 5 skipped pages");
    assert_eq!(rows[3], "! Links        › 1 broken internal link");
    assert!(
        warm.stdout.contains("  missing:9 → /docs/nowhere"),
        "{}",
        warm.stdout
    );
    assert!(read(&site.join("llms.txt")).contains("- [Missing](/docs/missing/)"));

    // Missing public file: the build fails naming it.
    fs::write(
        project.join("docs.yaml"),
        read(&project.join("docs.yaml")).replace("docs/cli.md", "docs/gone.md"),
    )
    .unwrap();
    let failed = folio(&project, &["build"]);
    assert_eq!(failed.code, 1);
    assert!(
        failed.stderr.contains(&format!(
            "Build failed: public file not found: {}/docs/gone.md",
            project.display()
        )),
        "{}",
        failed.stderr
    );
    // A public: source must stay inside the project: `..` and absolute paths fail.
    for (source, message) in [
        ("../x", "public must stay within the project directory"),
        (
            "/etc/hosts",
            "public must stay within the project directory",
        ),
        (
            ".build/public/cli.md",
            "public cannot point inside the .build directory",
        ),
    ] {
        fs::write(
            project.join("docs.yaml"),
            format!("project:\n  name: X\nsource:\n  docs: [docs]\npublic:\n  - \"{source}\"\n"),
        )
        .unwrap();
        let escaped = folio(&project, &["build"]);
        assert_eq!(escaped.code, 1, "{source}");
        assert!(
            escaped.stderr.contains(&format!("Build failed: {message}")),
            "{source}: {}",
            escaped.stderr
        );
    }
    // A non-list public: is a config error.
    fs::write(
        project.join("docs.yaml"),
        "project:\n  name: X\nsource:\n  docs: [docs]\npublic: install.sh\n",
    )
    .unwrap();
    let bad = folio(&project, &["build"]);
    assert_eq!(bad.code, 1);
    assert!(bad
        .stderr
        .contains("Build failed: public must be a list of strings"));
}

#[test]
fn failures_name_the_cause() {
    let (_dir, project) = example_project();
    // Invalid Python names the file.
    let broken = project.join("src/example_package/broken.py");
    fs::write(&broken, "class Broken(\n").unwrap();
    let run = folio(&project, &["build"]);
    assert_eq!(run.code, 1);
    assert!(run.stderr.contains("Build failed: "), "{}", run.stderr);
    assert!(run.stderr.contains("broken.py"), "{}", run.stderr);
    assert!(
        !project.join(".build/content/index.mdx").exists(),
        "nothing is written before parsing succeeds"
    );
    fs::remove_file(&broken).unwrap();

    // Missing config.
    let empty = tempfile::tempdir().unwrap();
    let missing = folio(empty.path(), &["build"]);
    assert_eq!(missing.code, 1);
    assert_eq!(
        missing.diagnostics().trim_end(),
        format!(
            "Error: Config file not found: {}",
            empty
                .path()
                .canonicalize()
                .unwrap()
                .join("docs.yaml")
                .display()
        )
    );
    // Conflicting directories.
    let conflict = folio(
        &project,
        &[
            "build",
            "--project-dir",
            empty.path().to_str().unwrap(),
            project.to_str().unwrap(),
        ],
    );
    assert_eq!(conflict.code, 1);
    assert!(conflict
        .stderr
        .contains("either as an argument or --project-dir"));

    // Empty project gate: one failure line, naming the config it read.
    fs::write(
        empty.path().join("other.yaml"),
        "project:\n  name: Empty\nsource:\n  docs: [nowhere]\n",
    )
    .unwrap();
    let gate = folio(empty.path(), &["build", "-c", "other.yaml"]);
    assert_eq!(gate.code, 1);
    let message = "No source modules or documentation found. Check the source paths in other.yaml.";
    assert!(
        gate.stderr.contains(&format!("Build failed: {message}")),
        "{}",
        gate.stderr
    );
    assert_eq!(
        format!("{}{}", gate.stdout, gate.stderr)
            .matches(message)
            .count(),
        1,
        "said once:\n{}{}",
        gate.stdout,
        gate.stderr
    );
    assert!(gate.stdout.contains("Documentation source path not found:"));
}

#[test]
fn a_javascript_root_builds_its_own_api_reference_pages() {
    let (_dir, project) = example_project();
    fs::write(
        project.join("docs.yaml"),
        read(&project.join("docs.yaml")).replace(
            "  docs:\n    - \"docs\"",
            "  javascript:\n    paths: [web]\n  docs:\n    - \"docs\"",
        ),
    )
    .unwrap();
    fs::create_dir_all(project.join("web")).unwrap();
    fs::write(
        project.join("web/util.js"),
        "/** Browser helpers. */\n\n/**\n * Slugify a title.\n * @param {string} title - The title.\n * @returns {string} The slug.\n */\nexport function slugify(title) {\n  return title;\n}\n",
    )
    .unwrap();
    fs::write(
        project.join("web/widget.jsx"),
        "export default function W() {}\n",
    )
    .unwrap();

    let run = folio(&project, &["build"]);
    run.ok();
    assert!(run.stdout.contains("JSX is not read in this release"));
    let page = read(&project.join(".build/content/api-reference/javascript/util.mdx"));
    assert!(
        page.contains("```javascript\nexport function slugify(title)\n```"),
        "{page}"
    );
    assert!(page.contains("Browser helpers."));
    let manifest = json(&project.join(".build/.folio-manifest.json"));
    let languages: BTreeSet<&str> = manifest["sources"]
        .as_object()
        .unwrap()
        .values()
        .filter_map(|v| v.get("language").and_then(Value::as_str))
        .collect();
    assert_eq!(languages, BTreeSet::from(["javascript", "python"]));
}

#[test]
fn asset_collisions_stale_sweep_manifest_guards_and_previews() {
    let (_dir, project) = example_project();
    let build = project.join(".build");
    let content = build.join("content");
    let manifest_path = build.join(".folio-manifest.json");

    // Two docs roots: `guide/a.md` and `guide/b.md` both claim `guide/logo.png`.
    fs::write(
        project.join("docs.yaml"),
        read(&project.join("docs.yaml")).replace(
            "  docs:\n    - \"docs\"",
            "  docs:\n    - \"docs\"\n    - \"extra\"",
        ),
    )
    .unwrap();
    fs::create_dir_all(project.join("docs/guide")).unwrap();
    fs::create_dir_all(project.join("extra/guide")).unwrap();
    let page = "![Logo](logo.png)\n\n![Shared](shared.png)\n";
    fs::write(project.join("docs/guide/a.md"), format!("# A\n\n{page}")).unwrap();
    fs::write(project.join("extra/guide/b.md"), format!("# B\n\n{page}")).unwrap();
    fs::write(project.join("docs/guide/logo.png"), b"logo-a").unwrap();
    fs::write(project.join("extra/guide/logo.png"), b"logo-b").unwrap();
    fs::write(project.join("docs/guide/shared.png"), b"shared").unwrap();
    fs::write(project.join("extra/guide/shared.png"), b"shared").unwrap();
    let collision = folio(&project, &["build"]);
    assert_eq!(collision.code, 1);
    assert!(
        collision.stderr.contains(&format!(
            "Build failed: Asset destination collision at {}/content/guide/logo.png: {}/docs/guide/a.md and {}/extra/guide/b.md contain different bytes",
            build.display(),
            project.display(),
            project.display()
        )),
        "{}",
        collision.stderr
    );
    assert!(
        !content.join("guide/a.mdx").exists() && !content.join("guide/logo.png").exists(),
        "nothing is written before every asset validates"
    );

    // Identical bytes from two pages are one shared asset.
    fs::write(project.join("extra/guide/logo.png"), b"logo-a").unwrap();
    folio(&project, &["build"]).ok();
    assert_eq!(fs::read(content.join("guide/logo.png")).unwrap(), b"logo-a");
    assert!(content.join("guide/shared.png").exists());
    let key = format!("{}/docs/guide/a.md", project.display());
    assert_eq!(
        json(&manifest_path)["sources"][&key]["assets"],
        serde_json::json!(["logo.png", "shared.png"])
    );

    // The stale sweep removes an asset only after every page released it.
    fs::write(
        project.join("docs/guide/a.md"),
        "# A\n\n![Logo](logo.png)\n",
    )
    .unwrap();
    folio(&project, &["build"]).ok();
    assert!(
        content.join("guide/shared.png").exists(),
        "b.md still claims it"
    );
    fs::write(
        project.join("extra/guide/b.md"),
        "# B\n\n![Logo](logo.png)\n",
    )
    .unwrap();
    folio(&project, &["build"]).ok();
    assert!(!content.join("guide/shared.png").exists());
    assert!(content.join("guide/logo.png").exists());
    assert_eq!(
        json(&manifest_path)["sources"][&key]["assets"],
        serde_json::json!(["logo.png"])
    );

    // A tampered manifest fails instead of deleting a page or escaping content/.
    let clean_manifest = read(&manifest_path);
    for (assets, message) in [
        (
            serde_json::json!("nope"),
            "Invalid generated asset ownership in build manifest",
        ),
        (
            serde_json::json!(["../victim.mdx"]),
            "Asset would be written outside the content directory: ../victim.mdx (from route guide/a)",
        ),
        (
            serde_json::json!(["index.mdx"]),
            "Asset path is reserved for generated content: index.mdx",
        ),
    ] {
        let mut tampered: Value = serde_json::from_str(&clean_manifest).unwrap();
        tampered["sources"][&key]["assets"] = assets;
        fs::write(&manifest_path, serde_json::to_string_pretty(&tampered).unwrap()).unwrap();
        let refused = folio(&project, &["build"]);
        assert_eq!(refused.code, 1, "{message}");
        assert!(
            refused.stderr.contains(&format!("Build failed: {message}")),
            "{}",
            refused.stdout
        );
        assert!(content.join("index.mdx").is_file() && content.join("guide/a.mdx").is_file());
    }
    fs::write(&manifest_path, clean_manifest).unwrap();

    // Previews: a project under docs/examples builds into public/_folio/examples/<name>/.
    fs::create_dir_all(project.join("docs/examples/mini/docs")).unwrap();
    fs::write(
        project.join("docs/examples/mini/docs.yaml"),
        "project:\n  name: Mini\nsource:\n  docs: [docs]\n",
    )
    .unwrap();
    fs::write(
        project.join("docs/examples/mini/docs/index.md"),
        "# Mini\n\nA preview.\n",
    )
    .unwrap();
    let previews = folio(&project, &["build"]);
    previews.ok();
    assert!(
        previews
            .rows()
            .contains(&"✓ Previews     › 1 example rebuilt"),
        "{}",
        previews.stdout
    );
    assert_eq!(
        previews.stdout.matches("████████╗").count(),
        1,
        "a nested build prints no banner"
    );
    let example = build.join("public/_folio/examples/mini");
    let files = json(&example.join("manifest.json"));
    let paths: Vec<&str> = files["files"]
        .as_array()
        .unwrap()
        .iter()
        .map(|f| f["path"].as_str().unwrap())
        .collect();
    assert_eq!(paths, ["docs/index.md", "docs.yaml"]);
    assert_eq!(
        files["files"][1]["url"],
        "/_folio/examples/mini/files/docs.yaml"
    );
    assert_eq!(files["files"][1]["language"], "yaml");
    assert_eq!(files["files"][0]["language"], "markdown");
    assert!(example.join("files/docs/index.md").is_file());
    assert!(
        example.join("llms.txt").is_file(),
        "the nested build exported into the example dir"
    );
    assert!(build
        .join(".preview-examples/mini/content/index.mdx")
        .is_file());
}

#[test]
#[ignore = "runs pnpm install and next build on the generated-site example; run locally with --ignored --nocapture"]
fn real_export_of_the_example_site() {
    let (_dir, project) = example_project();
    let started = std::time::Instant::now();
    let output = Command::new(env!("CARGO_BIN_EXE_folio"))
        .current_dir(&project)
        .args(["build"])
        .env("NO_COLOR", "1")
        .env_remove("FOLIO_FRONTEND_RUNTIME")
        .output()
        .unwrap();
    let elapsed = started.elapsed();
    let stdout = String::from_utf8(output.stdout).unwrap();
    eprintln!("{stdout}\nreal export took {elapsed:?}");
    assert!(output.status.success(), "{stdout}");
    assert!(stdout.contains("Build output"));
    assert!(stdout.contains("✓ Dependencies › installed"));
    let site = project.join("_site");
    for rel in [
        "index.html",
        "docs/index.html",
        "docs/api-reference/example_package/arithmetic/index.html",
        "_folio/contract.json",
        "_folio/markdown/cli.md",
        "sitemap.xml",
    ] {
        assert!(site.join(rel).is_file(), "missing {rel}");
    }
    assert!(project.join(".build/.folio-build.log").is_file());
}
