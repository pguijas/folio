//! Persistent runner workspaces must not carry files into the next build.

#[cfg(unix)]
#[test]
fn pages_jobs_clear_their_own_workspace_without_touching_other_jobs() {
    use serde_yaml_ng::Value;
    use std::{fs, path::Path, process::Command};

    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let directories = [
        "production-source",
        "preview-source",
        "trusted-source",
        "_preview-site",
        "_pages-artifact",
        "_pages-state",
        "unrelated-job",
    ];
    for (file, job, removed) in [
        ("pages.yml", "deploy", &["production-source"][..]),
        (
            "branch-previews.yml",
            "build-preview",
            &["preview-source"][..],
        ),
        (
            "branch-previews.yml",
            "deploy",
            &[
                "trusted-source",
                "_preview-site",
                "_pages-artifact",
                "_pages-state",
            ][..],
        ),
    ] {
        let workflow: Value = serde_yaml_ng::from_str(
            &fs::read_to_string(root.join(".github/workflows").join(file)).unwrap(),
        )
        .unwrap();
        let steps = workflow["jobs"][job]["steps"].as_sequence().unwrap();
        let reset = steps
            .iter()
            .position(|step| step["name"].as_str() == Some("Clear job workspace"))
            .expect("clear the persistent workspace before checkout or download");
        let checkout = steps
            .iter()
            .position(|step| step["uses"].as_str() == Some("actions/checkout@v4"))
            .unwrap();
        assert!(reset < checkout);

        let workspace = tempfile::tempdir().unwrap();
        for directory in directories {
            let path = workspace.path().join(directory).join("nested");
            fs::create_dir_all(&path).unwrap();
            fs::write(path.join("stale.html"), "previous run").unwrap();
        }
        let status = Command::new("bash")
            .args([
                "-euo",
                "pipefail",
                "-c",
                steps[reset]["run"].as_str().unwrap(),
            ])
            .env("GITHUB_WORKSPACE", workspace.path())
            .current_dir(workspace.path())
            .status()
            .unwrap();
        assert!(status.success(), "{file}: {job} cleanup failed");
        for directory in directories {
            assert_eq!(
                workspace.path().join(directory).exists(),
                !removed.contains(&directory),
                "{file}: {job} must only clear its own {removed:?}, checked {directory}"
            );
        }
    }
}

#[cfg(unix)]
#[test]
fn preview_build_paths_follow_pages_configuration_for_custom_and_project_domains() {
    use serde_yaml_ng::Value;
    use std::{fs, path::Path, process::Command};

    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let binary = Path::new(env!("CARGO_BIN_EXE_folioh"));
    let path = format!(
        "{}:{}",
        binary.parent().unwrap().display(),
        std::env::var("PATH").unwrap_or_default()
    );
    for file in [
        ".github/workflows/branch-previews.yml",
        "crates/folioh-cli/src/workflows/branch-previews.yml",
    ] {
        let workflow: Value =
            serde_yaml_ng::from_str(&fs::read_to_string(root.join(file)).unwrap()).unwrap();
        let steps = workflow["jobs"]["build-preview"]["steps"]
            .as_sequence()
            .unwrap();
        let compute = steps
            .iter()
            .find(|step| step["name"].as_str() == Some("Compute preview path"))
            .unwrap();
        for (base_path, base_url) in [
            ("/", "https://folioh.site"),
            ("/folioh", "https://pguijas.github.io/folioh"),
        ] {
            let output = Command::new("bash")
                .args(["-euo", "pipefail", "-c", compute["run"].as_str().unwrap()])
                .env("PATH", &path)
                .env("HEAD_REF", "feature/demo")
                .env("PR_NUMBER", "17")
                .env("PAGES_BASE_PATH", base_path)
                .env("PAGES_BASE_URL", base_url)
                .env_remove("GITHUB_OUTPUT")
                .output()
                .unwrap();
            assert!(
                output.status.success(),
                "{file}: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            let stdout = String::from_utf8(output.stdout).unwrap();
            assert!(
                stdout.contains(&format!(
                    "base_path={}/previews/pr-17-feature-demo",
                    base_path.trim_end_matches('/')
                )),
                "{file}: {stdout}"
            );
            assert!(
                stdout.contains(&format!("url={base_url}/previews/pr-17-feature-demo/")),
                "{file}: {stdout}"
            );
        }
    }
}
