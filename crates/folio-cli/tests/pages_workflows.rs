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
