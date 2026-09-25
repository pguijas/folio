use super::*;

fn make_preview(previews: &Path, name: &str, metadata: Option<serde_json::Value>) -> PathBuf {
    let preview = previews.join(name);
    fs::create_dir_all(&preview).unwrap();
    fs::write(preview.join("index.html"), "x").unwrap();
    if let Some(metadata) = metadata {
        fs::write(preview.join(PREVIEW_METADATA_FILE), metadata.to_string()).unwrap();
    }
    preview
}

#[test]
fn preview_paths_normalise_branch_and_base_path() {
    let cases = [
        (
            (
                "Feature/Foo",
                "17",
                "/folio/",
                "https://pguijas.github.io/folio/",
            ),
            (
                "pr-17-feature-foo",
                "/folio/previews/pr-17-feature-foo",
                "https://pguijas.github.io/folio/previews/pr-17-feature-foo/",
            ),
        ),
        (
            ("---", "23", "/", "https://example.com/project"),
            (
                "pr-23",
                "/previews/pr-23",
                "https://example.com/project/previews/pr-23/",
            ),
        ),
        (
            (
                "Feature/API",
                "17",
                "/folio/",
                "https://pguijas.github.io/folio/",
            ),
            (
                "pr-17-feature-api",
                "/folio/previews/pr-17-feature-api",
                "https://pguijas.github.io/folio/previews/pr-17-feature-api/",
            ),
        ),
        (
            (
                "feature_api",
                "18",
                "folio",
                "https://pguijas.github.io/folio",
            ),
            (
                "pr-18-feature-api",
                "/folio/previews/pr-18-feature-api",
                "https://pguijas.github.io/folio/previews/pr-18-feature-api/",
            ),
        ),
    ];
    for ((head_ref, pr, base, url), (id, base_path, expected_url)) in cases {
        let preview = compute_preview_path(head_ref, pr, base, url);
        assert_eq!(preview.safe_branch, id);
        assert_eq!(preview.base_path, base_path);
        assert_eq!(preview.url, expected_url);
    }
}

#[test]
fn long_ids_are_capped_with_a_digest() {
    let long_branch = format!("feature/{}", "very-long-branch-name-".repeat(12));
    let id = safe_preview_branch(&long_branch, "17");
    assert!(id.starts_with("pr-17-feature-"));
    assert!(id.len() <= 80);
    assert_eq!(id.len(), 80);
    let other = safe_preview_branch(&format!("{long_branch}x"), "17");
    assert_ne!(id, other, "the digest keeps overflow ids distinct");

    let long_pr = "17".repeat(60);
    let id = safe_preview_branch("Feature/Foo", &long_pr);
    assert!(id.starts_with("pr-171717171717171-"));
    assert!(id.len() <= 80);
    assert!(validate_preview_id(&id).is_ok());
    // A truncated SHA-256 of `<pr>:<ref>`.
    let digest = hex(&Sha256::digest(format!("{long_pr}:Feature/Foo")));
    assert!(id.contains(&digest[..8]));

    assert_eq!(safe_preview_branch("", "unknown ref"), "pr-unknown-ref");
    assert_eq!(safe_preview_branch("x", "!!!"), "pr-unknown-x");
}

#[test]
fn preview_ids_from_the_command_line_are_validated() {
    assert!(validate_preview_id("pr-17-feature-foo").is_ok());
    for bad in ["../outside", "Pr-1", "-lead", "", "a_b", &"a".repeat(81)] {
        assert_eq!(
            validate_preview_id(bad).unwrap_err(),
            format!("Invalid preview id: {bad}")
        );
    }
}

#[test]
fn previews_data_collects_sidecars_newest_first() {
    let dir = tempfile::tempdir().unwrap();
    let previews = dir.path().join("previews");
    make_preview(
        &previews,
        "pr-17-feature-foo",
        Some(serde_json::json!({
            "pr_number": "17", "title": "Add cool feature", "branch": "feature/foo", "commit": "abcdef1",
            "commit_url": "https://github.com/acme/widgets/commit/abcdef1",
            "pr_url": "https://github.com/acme/widgets/pull/17", "author": "octocat",
            "avatar_url": "https://avatars.example/octocat.png", "updated_at": "2026-07-01T12:00:00Z",
            "repo": 5
        })),
    );
    make_preview(
        &previews,
        "pr-1-old",
        Some(serde_json::json!({"updated_at": "2026-01-01T00:00:00Z", "title": "  "})),
    );
    make_preview(&previews, "pr-3-bare", None);
    fs::create_dir(previews.join("no-index")).unwrap();
    fs::write(previews.join("stray.txt"), "").unwrap();

    let entries = write_previews_data(&previews).unwrap();
    let names: Vec<&str> = entries.iter().map(|e| e.name.as_str()).collect();
    assert_eq!(names, ["pr-17-feature-foo", "pr-1-old", "pr-3-bare"]);
    let foo = &entries[0];
    assert_eq!(foo.href, "./pr-17-feature-foo/");
    assert_eq!(foo.title, "Add cool feature");
    assert_eq!(foo.author, "octocat");
    assert_eq!(foo.repo, "", "non-string fields are ignored");
    assert!(foo.commit_url.ends_with("/commit/abcdef1"));
    assert_eq!(
        entries[1].title, "pr-1-old",
        "a blank title falls back to the name"
    );
    assert_eq!(entries[2].title, "pr-3-bare");
    assert_eq!(entries[2].pr_number, "");

    let on_disk = fs::read_to_string(previews.join(PREVIEWS_DATA_FILE)).unwrap();
    assert!(on_disk.ends_with("]\n"));
    assert!(on_disk.starts_with("[\n  {\n    \"name\": \"pr-17-feature-foo\",\n    \"href\": \"./pr-17-feature-foo/\",\n    \"title\": \"Add cool feature\",\n    \"pr_number\": \"17\","));
    let parsed: Vec<PreviewEntry> = serde_json::from_str::<serde_json::Value>(&on_disk)
        .unwrap()
        .as_array()
        .unwrap()
        .iter()
        .map(|v| {
            let obj = v.as_object().unwrap();
            let s = |k: &str| obj[k].as_str().unwrap().to_string();
            PreviewEntry {
                name: s("name"),
                href: s("href"),
                title: s("title"),
                pr_number: s("pr_number"),
                branch: s("branch"),
                commit: s("commit"),
                commit_url: s("commit_url"),
                pr_url: s("pr_url"),
                repo: s("repo"),
                repo_url: s("repo_url"),
                author: s("author"),
                author_url: s("author_url"),
                avatar_url: s("avatar_url"),
                updated_at: s("updated_at"),
            }
        })
        .collect();
    assert_eq!(parsed, entries);

    let empty = dir.path().join("empty");
    assert_eq!(
        write_previews_data(&empty).unwrap(),
        Vec::<PreviewEntry>::new()
    );
    assert_eq!(
        fs::read_to_string(empty.join(PREVIEWS_DATA_FILE)).unwrap(),
        "[]\n"
    );
}

#[test]
fn preview_metadata_sidecar_is_enriched_sorted_and_guarded() {
    let dir = tempfile::tempdir().unwrap();
    let artifact = dir.path().join("_pages-artifact");
    let preview = artifact.join("previews/pr-17-feature-foo");
    fs::create_dir_all(&preview).unwrap();
    let metadata = PreviewMetadata {
        pr_number: "17",
        title: "Add feature",
        branch: "feature/foo",
        commit: "abcdef1234567890",
        pr_url: "https://github.com/acme/widgets/pull/17",
        updated_at: "2026-07-01T12:00:00Z",
        repo: "acme/widgets",
        author: "octocat",
        author_url: "https://github.com/octocat",
        avatar_url: "https://avatars.example/octocat.png",
    };
    write_preview_metadata(&artifact, "pr-17-feature-foo", &metadata).unwrap();
    let text = fs::read_to_string(preview.join(PREVIEW_METADATA_FILE)).unwrap();
    assert_eq!(
            text,
            "{\n  \"author\": \"octocat\",\n  \"author_url\": \"https://github.com/octocat\",\n  \"avatar_url\": \"https://avatars.example/octocat.png\",\n  \"branch\": \"feature/foo\",\n  \"commit\": \"abcdef123456\",\n  \"commit_url\": \"https://github.com/acme/widgets/commit/abcdef1234567890\",\n  \"pr_number\": \"17\",\n  \"pr_url\": \"https://github.com/acme/widgets/pull/17\",\n  \"repo\": \"acme/widgets\",\n  \"repo_url\": \"https://github.com/acme/widgets\",\n  \"title\": \"Add feature\",\n  \"updated_at\": \"2026-07-01T12:00:00Z\"\n}\n"
        );

    let err = write_preview_metadata(&artifact, "../outside", &metadata).unwrap_err();
    assert!(err.contains("Invalid preview id"));
    let err = write_preview_metadata(&artifact, "pr-9-missing", &metadata).unwrap_err();
    assert!(err.starts_with("Preview directory not found: "));
    let bare = PreviewMetadata {
        repo: "",
        commit: "",
        ..metadata
    };
    write_preview_metadata(&artifact, "pr-17-feature-foo", &bare).unwrap();
    let text = fs::read_to_string(preview.join(PREVIEW_METADATA_FILE)).unwrap();
    assert!(text.contains("\"commit_url\": \"\""));
    assert!(text.contains("\"repo_url\": \"\""));
}

#[test]
fn prune_removes_stale_directories_only() {
    let dir = tempfile::tempdir().unwrap();
    let previews = dir.path().join("previews");
    make_preview(&previews, "pr-1-foo", None);
    make_preview(&previews, "pr-2-bar", None);
    make_preview(&previews, "pr-9-gone", None);
    fs::create_dir(previews.join("no-index")).unwrap();
    fs::write(previews.join(PREVIEWS_DATA_FILE), "[]").unwrap();
    let keep = ["pr-1-foo", "pr-2-bar"]
        .map(str::to_string)
        .into_iter()
        .collect();
    assert_eq!(
        prune_previews(&previews, &keep).unwrap(),
        ["no-index", "pr-9-gone"]
    );
    assert!(previews.join("pr-1-foo").is_dir());
    assert!(previews.join("pr-2-bar").is_dir());
    assert!(!previews.join("pr-9-gone").exists());
    assert!(previews.join(PREVIEWS_DATA_FILE).is_file());
    assert_eq!(
        prune_previews(&dir.path().join("missing"), &keep).unwrap(),
        Vec::<String>::new()
    );
}

#[test]
fn prepare_artifact_prefers_the_saved_root_and_restores_previews() {
    let dir = tempfile::tempdir().unwrap();
    let production = dir.path().join("production/_site");
    fs::create_dir_all(&production).unwrap();
    fs::write(production.join("index.html"), "production").unwrap();
    let state = dir.path().join("_pages-state");
    fs::create_dir_all(state.join("previews/old-preview")).unwrap();
    fs::write(state.join("previews/old-preview/index.html"), "old").unwrap();
    fs::write(state.join("previews/index.html"), "reserved").unwrap();

    let artifact = dir.path().join("_pages-artifact");
    prepare_pages_artifact(
        &production,
        &artifact,
        dir.path(),
        &state,
        STATE_BRANCH,
        false,
    )
    .unwrap();
    assert_eq!(
        fs::read_to_string(artifact.join("index.html")).unwrap(),
        "production"
    );
    assert_eq!(
        fs::read_to_string(artifact.join("previews/old-preview/index.html")).unwrap(),
        "old"
    );
    assert!(
        !artifact.join("previews/index.html").exists(),
        "reserved names stay out"
    );
    assert!(artifact.join(".nojekyll").exists());

    fs::write(state.join(".git"), "gitdir: ignored\n").unwrap();
    fs::write(state.join("index.html"), "already deployed").unwrap();
    fs::write(production.join("index.html"), "rebuilt main").unwrap();
    prepare_pages_artifact(
        &production,
        &artifact,
        dir.path(),
        &state,
        STATE_BRANCH,
        false,
    )
    .unwrap();
    assert_eq!(
        fs::read_to_string(artifact.join("index.html")).unwrap(),
        "already deployed"
    );
    assert!(!artifact.join(".git").exists());
    assert_eq!(
        fs::read_to_string(artifact.join("previews/old-preview/index.html")).unwrap(),
        "old"
    );
    assert!(artifact.join(".nojekyll").exists());

    let missing = dir.path().join("nope");
    let err = prepare_pages_artifact(
        &missing,
        &artifact,
        dir.path(),
        &dir.path().join("no-state"),
        STATE_BRANCH,
        false,
    )
    .unwrap_err();
    assert!(err.starts_with("Source directory not found: "));
}

#[test]
fn preserve_previews_copies_the_state_previews_into_the_site() {
    let dir = tempfile::tempdir().unwrap();
    let site = dir.path().join("_site");
    let state = dir.path().join("_pages-state");
    fs::create_dir_all(state.join("previews/pr-1-a")).unwrap();
    fs::write(state.join("previews/pr-1-a/index.html"), "a").unwrap();
    fs::write(state.join("previews/previews.json"), "[]").unwrap();
    preserve_branch_previews(&site, dir.path(), &state, STATE_BRANCH, false).unwrap();
    assert_eq!(
        fs::read_to_string(site.join("previews/pr-1-a/index.html")).unwrap(),
        "a"
    );
    assert!(!site.join("previews/previews.json").exists());
    assert!(site.join(".nojekyll").exists());
}

#[test]
fn copy_branch_preview_replaces_the_preview_and_rejects_traversal() {
    let dir = tempfile::tempdir().unwrap();
    let preview_site = dir.path().join("preview/_site");
    fs::create_dir_all(&preview_site).unwrap();
    fs::write(preview_site.join("index.html"), "new").unwrap();
    let artifact = dir.path().join("_pages-artifact");
    let old = artifact.join("previews/feature-a");
    fs::create_dir_all(&old).unwrap();
    fs::write(old.join("stale.html"), "stale").unwrap();

    copy_branch_preview(&preview_site, &artifact, "feature-a").unwrap();
    assert_eq!(fs::read_to_string(old.join("index.html")).unwrap(), "new");
    assert!(!old.join("stale.html").exists());

    let outside = dir.path().join("outside");
    fs::create_dir(&outside).unwrap();
    fs::write(outside.join("sentinel.txt"), "keep").unwrap();
    let err = copy_branch_preview(&preview_site, &artifact, "../outside").unwrap_err();
    assert!(err.contains("Invalid preview id"));
    assert_eq!(
        fs::read_to_string(outside.join("sentinel.txt")).unwrap(),
        "keep"
    );

    let long_id = safe_preview_branch("Feature/Foo", &"17".repeat(60));
    copy_branch_preview(&preview_site, &artifact, &long_id).unwrap();
    assert_eq!(
        fs::read_to_string(artifact.join("previews").join(&long_id).join("index.html")).unwrap(),
        "new"
    );
}

#[cfg(unix)]
#[test]
fn copies_keep_symlinks_as_symlinks() {
    let dir = tempfile::tempdir().unwrap();
    let src = dir.path().join("src");
    fs::create_dir_all(src.join("sub")).unwrap();
    fs::write(src.join("sub/file.txt"), "f").unwrap();
    std::os::unix::fs::symlink("sub/file.txt", src.join("link")).unwrap();
    let dst = dir.path().join("dst");
    copy_contents(&src, &dst, &[]).unwrap();
    assert!(fs::symlink_metadata(dst.join("link"))
        .unwrap()
        .file_type()
        .is_symlink());
    assert_eq!(fs::read_to_string(dst.join("sub/file.txt")).unwrap(), "f");
    remove_path(&dst.join("link")).unwrap();
    assert!(
        dst.join("sub/file.txt").exists(),
        "unlinking a symlink leaves its target"
    );
}

#[test]
fn comment_body_carries_the_marker_and_links() {
    let body = preview_comment_body(
        "https://example.com/previews/feature-a/",
        "https://example.com/previews/",
        "Feature/A",
        "1234567890abcdef",
    );
    assert_eq!(
            body,
            "<!-- folio-branch-preview -->\n### Branch preview\n\nPreview: [Preview](https://example.com/previews/feature-a/)\n\nPreview index: [Preview index](https://example.com/previews/)\n\nBranch: `Feature/A`\nCommit: `1234567`"
        );
}

#[test]
fn upsert_updates_an_existing_comment_or_creates_one() {
    let mut calls: Vec<Vec<String>> = Vec::new();
    let mut gh = |args: &[String]| {
        calls.push(args.to_vec());
        Ok(
            if args
                .get(1)
                .is_some_and(|a| a == "repos/acme/widgets/issues/17/comments")
            {
                "12345\n".to_string()
            } else {
                String::new()
            },
        )
    };
    let body = format!("{COMMENT_MARKER}\nupdated");
    assert_eq!(
        upsert_preview_comment(&mut gh, "acme/widgets", "17", &body).unwrap(),
        "updated"
    );
    assert_eq!(
        calls[1],
        [
            "api",
            "--method",
            "PATCH",
            "repos/acme/widgets/issues/comments/12345",
            "-f",
            &format!("body={body}")
        ]
    );
    assert!(calls[0]
        .iter()
        .any(|part| part.contains(".user.login == \"github-actions[bot]\"")));
    assert_eq!(
        calls[0][..4],
        [
            "api",
            "repos/acme/widgets/issues/17/comments",
            "--paginate",
            "--jq"
        ]
    );

    let mut calls: Vec<Vec<String>> = Vec::new();
    let mut gh = |args: &[String]| {
        calls.push(args.to_vec());
        Ok(String::new())
    };
    let body = format!("{COMMENT_MARKER}\ncreated");
    assert_eq!(
        upsert_preview_comment(&mut gh, "acme/widgets", "17", &body).unwrap(),
        "created"
    );
    assert_eq!(
        calls[1],
        [
            "api",
            "--method",
            "POST",
            "repos/acme/widgets/issues/17/comments",
            "-f",
            &format!("body={body}")
        ]
    );
}
