//! The real pnpm/next runtime against a shim `pnpm` (Unix only).
#![cfg(unix)]

mod common;

use std::path::{Path, PathBuf};

use folio_site::runtime::{FrontendRuntime, NextRuntime};

/// A `pnpm` stand-in that logs its argv and mimics the calls the runtime makes.
fn shim(dir: &Path, next_exit: i32, build_exit: i32) -> (PathBuf, PathBuf) {
    use std::os::unix::fs::PermissionsExt;
    let log = dir.join("pnpm.log");
    let script = format!(
        "#!/bin/sh\necho \"$*\" >> {log}\ncase \"$*\" in\n  \"--version\") echo 10.0.0 ;;\n  \"exec next --version\") exit {next_exit} ;;\n  \"install --frozen-lockfile\") [ -e node_modules ] && [ ! -e node_modules/.bin/next ] && exit 3; mkdir -p node_modules/.bin; : > node_modules/.bin/next ;;\n  \"run build\") [ -e out ] && exit 4; [ -e .next/dev ] && exit 5; echo \"> folio@0.0.1 build\"; echo \"Creating an optimized production build ...\"; echo \"Compiled successfully\"; echo \"warned\" >&2; exit {build_exit} ;;\n  exec\\ next\\ dev*) [ -e out ] && exit 4; [ -e .next/dev ] && exit 5; echo \"ready on $6\"; echo \"dev warning\" >&2 ;;\nesac\nexit 0\n",
        log = log.display()
    );
    let path = dir.join("pnpm");
    std::fs::write(&path, script).unwrap();
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755)).unwrap();
    (path, log)
}

fn runtime(pnpm: &Path) -> NextRuntime {
    NextRuntime {
        pnpm: pnpm.to_string_lossy().into_owned(),
        preflight: false,
    }
}

fn calls(log: &Path) -> Vec<String> {
    std::fs::read_to_string(log)
        .unwrap_or_default()
        .lines()
        .map(str::to_string)
        .collect()
}

#[test]
fn install_deps_repairs_incomplete_and_broken_node_modules_and_skips_when_current() {
    let dir = tempfile::tempdir().unwrap();
    let template = common::make_template(dir.path());
    common::write(&template, "pnpm-lock.yaml", "lock");
    let build = dir.path().join("build");
    common::write(&build, "pnpm-lock.yaml", "lock");
    std::fs::create_dir_all(build.join("node_modules")).unwrap();
    let (pnpm, log) = shim(dir.path(), 0, 0);
    assert!(
        runtime(&pnpm)
            .install_deps(&template, &build, &mut |_| {})
            .unwrap()
            .installed
    );
    assert_eq!(calls(&log), ["install --frozen-lockfile"]);
    assert!(build.join("node_modules/.bin/next").exists());

    // A working next and an unchanged lockfile need no install.
    std::fs::remove_file(&log).unwrap();
    assert!(
        !runtime(&pnpm)
            .install_deps(&template, &build, &mut |_| {})
            .unwrap()
            .installed
    );
    assert_eq!(calls(&log), ["exec next --version"]);

    // A changed template lockfile reinstalls.
    common::write(&template, "pnpm-lock.yaml", "lock-v2");
    std::fs::remove_file(&log).unwrap();
    assert!(
        runtime(&pnpm)
            .install_deps(&template, &build, &mut |_| {})
            .unwrap()
            .installed
    );
    assert_eq!(
        calls(&log),
        ["exec next --version", "install --frozen-lockfile"]
    );
    assert_eq!(
        common::read(&build.join("pnpm-lock.yaml")),
        "lock",
        "the build lockfile is the copy prepare made"
    );

    // A broken next runtime is removed and reinstalled.
    let broken = tempfile::tempdir().unwrap();
    let (pnpm, log) = shim(broken.path(), 1, 0);
    let build = broken.path().join("build");
    common::write(&build, "pnpm-lock.yaml", "lock-v2");
    common::write(&build, "node_modules/.bin/next", "#!/bin/sh\n");
    assert!(
        runtime(&pnpm)
            .install_deps(&template, &build, &mut |_| {})
            .unwrap()
            .installed
    );
    assert_eq!(
        calls(&log),
        ["exec next --version", "install --frozen-lockfile"]
    );
}

#[test]
fn install_deps_patches_the_nextra_loader_once() {
    let dir = tempfile::tempdir().unwrap();
    let template = common::make_template(dir.path());
    common::write(&template, "pnpm-lock.yaml", "lock");
    let build = dir.path().join("build");
    common::write(&build, "pnpm-lock.yaml", "lock");
    common::write(&build, "node_modules/.bin/next", "#!/bin/sh\n");
    let loader = common::write(
        &build,
        "node_modules/nextra/dist/server/loader.js",
        "const lastCommitTime = IS_PRODUCTION ? await getLastCommitTime(resourcePath) : NOW;\n",
    );
    let schema = common::write(
        &build,
        "node_modules/.pnpm/nextra-theme-docs@4/node_modules/nextra-theme-docs/dist/schemas.js",
        "x = { children: reactNode, other: 1 }\n",
    );
    let (pnpm, _) = shim(dir.path(), 0, 0);
    assert!(
        !runtime(&pnpm)
            .install_deps(&template, &build, &mut |_| {})
            .unwrap()
            .installed
    );
    let patched = common::read(&loader);
    assert_eq!(patched, "const isGeneratedFolioContent = resourcePath.includes(`${CWD}/content/`);\n  const lastCommitTime = IS_PRODUCTION ? isGeneratedFolioContent ? void 0 : await getLastCommitTime(resourcePath) : NOW;\n");
    assert_eq!(
        common::read(&schema),
        "x = { children: reactNode.optional(), other: 1 }\n"
    );
    runtime(&pnpm)
        .install_deps(&template, &build, &mut |_| {})
        .unwrap();
    assert_eq!(common::read(&loader), patched);
}

#[test]
fn build_streams_the_log_and_removes_stale_artifacts() {
    let dir = tempfile::tempdir().unwrap();
    let build = dir.path().join("build");
    common::write(
        &build,
        "out/index.html",
        "<script>self.__next_f.push([1,\"has-data-[icon=inline-start]\"])</script>",
    );
    common::write(&build, ".next/dev/app.css", ".x {}");
    let (pnpm, log) = shim(dir.path(), 0, 0);
    let log_path = build.join(".folio-build.log");
    let mut reported = Vec::new();
    runtime(&pnpm)
        .build(&build, &log_path, &mut |line| {
            reported.push(line.to_string())
        })
        .unwrap();
    let mut lines = reported.clone();
    lines.sort();
    assert_eq!(
        lines,
        [
            "> folio@0.0.1 build\n",
            "Compiled successfully\n",
            "Creating an optimized production build ...\n",
            "warned\n"
        ]
    );
    assert_eq!(common::read(&log_path), reported.concat());
    assert_eq!(calls(&log), ["run build"]);
    assert!(!build.join("out").exists() && !build.join(".next/dev").exists());

    std::fs::create_dir_all(dir.path().join("failing")).unwrap();
    let (failing, _) = shim(&dir.path().join("failing"), 0, 2);
    let err = runtime(&failing)
        .build(&build, &log_path, &mut |_| {})
        .unwrap_err();
    let text = err.to_string();
    assert!(
        text.starts_with("pnpm build failed:\n")
            && text.contains("Compiled successfully\n")
            && text.ends_with(&format!("\nFull log: {}", log_path.display())),
        "{text}"
    );
    assert!(matches!(err, folio_site::SiteError::Build { .. }));
}

#[test]
fn dev_server_port_handling_and_stale_artifacts() {
    let dir = tempfile::tempdir().unwrap();
    let build = dir.path().join("build");
    common::write(&build, "out/index.html", "stale");
    common::write(&build, ".next/dev/page-data.json", "");
    let (pnpm, log) = shim(dir.path(), 0, 0);
    let runtime = runtime(&pnpm);
    let lines = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
    let sink = std::sync::Arc::clone(&lines);
    let mut child = runtime
        .serve_with(
            &build,
            4321,
            false,
            &|_| false,
            &|port| panic!("killed {port}"),
            Box::new(move |line| sink.lock().unwrap().push(line.to_string())),
        )
        .unwrap();
    assert!(child.wait().unwrap().success());
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
    while lines.lock().unwrap().len() < 2 && std::time::Instant::now() < deadline {
        std::thread::sleep(std::time::Duration::from_millis(10));
    }
    let mut relayed = lines.lock().unwrap().clone();
    relayed.sort();
    assert_eq!(
        relayed,
        ["dev warning\n", "ready on 4321\n"],
        "stdout and stderr are relayed"
    );
    assert_eq!(calls(&log), ["exec next dev --turbopack --port 4321"]);
    assert!(!build.join("out").exists() && !build.join(".next/dev").exists());

    let err = runtime
        .serve_with(
            &build,
            4321,
            false,
            &|_| true,
            &|port| panic!("killed {port}"),
            Box::new(|_| {}),
        )
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Port 4321 is already in use. Stop the existing process or rerun with --kill-existing."
    );

    let killed = std::cell::Cell::new(0u16);
    let mut child = runtime
        .serve_with(
            &build,
            5678,
            true,
            &|_| true,
            &|port| {
                killed.set(port);
                true
            },
            Box::new(|_| {}),
        )
        .unwrap();
    assert!(child.wait().unwrap().success());
    assert_eq!(killed.get(), 5678);
    assert_eq!(
        calls(&log),
        [
            "exec next dev --turbopack --port 4321",
            "exec next dev --turbopack --port 5678"
        ]
    );

    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let err = runtime
        .serve(&build, port, false, Box::new(|_| {}))
        .unwrap_err()
        .to_string();
    assert_eq!(err, format!("Port {port} is already in use. Stop the existing process or rerun with --kill-existing."));
}
