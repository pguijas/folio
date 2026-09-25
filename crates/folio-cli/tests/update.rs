//! Black-box runs of `folio --update` against a release server the test
//! hosts, which redirects the way GitHub does: a binary that is up to date or
//! ahead of the latest release reports so and stays; a newer release replaces
//! a copy of the binary in place; a missing release, an unknown repository, a
//! checksum mismatch, a missing `SHA256SUMS`, an archive without the binary, a
//! binary that does not start and a directory that cannot be written all fail
//! before the installed binary is touched; a subcommand next to the flag is a
//! usage error. Unix only: the published "binary" is a shell script.
#![cfg(unix)]

mod common;

use std::collections::HashMap;
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;
use std::thread;

use sha2::{Digest, Sha256};

use common::Run;

const VERSION: &str = env!("CARGO_PKG_VERSION");
/// A closed loopback port: a run that reaches for the network fails at once
/// instead of contacting GitHub.
const NOWHERE: &str = "http://127.0.0.1:1/releases";

/// What the server answers at one path.
enum Reply {
    Redirect(String),
    Bytes(Vec<u8>),
    Missing,
}

/// A release server on a loopback port: GitHub's redirect from
/// `releases/latest`, the archive and `SHA256SUMS` under `releases/download`.
struct ReleaseServer {
    releases: String,
}

impl ReleaseServer {
    fn start(routes: HashMap<String, Reply>) -> ReleaseServer {
        let listener = TcpListener::bind("127.0.0.1:0").expect("a loopback port");
        let port = listener.local_addr().unwrap().port();
        let routes = Arc::new(routes);
        thread::spawn(move || {
            for stream in listener.incoming() {
                let Ok(stream) = stream else { break };
                let routes = Arc::clone(&routes);
                thread::spawn(move || respond(stream, &routes));
            }
        });
        ReleaseServer {
            releases: format!("http://127.0.0.1:{port}/releases"),
        }
    }
}

fn respond(mut stream: TcpStream, routes: &HashMap<String, Reply>) {
    let Ok(clone) = stream.try_clone() else {
        return;
    };
    let mut reader = BufReader::new(clone);
    let mut request = String::new();
    if reader.read_line(&mut request).is_err() {
        return;
    }
    loop {
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) | Err(_) => return,
            Ok(_) if line == "\r\n" || line == "\n" => break,
            Ok(_) => {}
        }
    }
    let path = request.split_whitespace().nth(1).unwrap_or("/");
    let (status, location, body): (&str, String, Vec<u8>) = match routes.get(path) {
        Some(Reply::Redirect(to)) => ("302 Found", format!("Location: {to}\r\n"), Vec::new()),
        Some(Reply::Bytes(bytes)) => ("200 OK", String::new(), bytes.clone()),
        Some(Reply::Missing) | None => ("404 Not Found", String::new(), b"Not Found".to_vec()),
    };
    let head = format!(
        "HTTP/1.1 {status}\r\nContent-Length: {}\r\nConnection: close\r\n{location}\r\n",
        body.len()
    );
    let _ = stream.write_all(head.as_bytes());
    let _ = stream.write_all(&body);
    let _ = stream.flush();
}

/// The archive `release.yml` packs for this machine, named as the binary asks.
fn asset() -> String {
    let triple = match (std::env::consts::OS, std::env::consts::ARCH) {
        ("linux", "x86_64") => "x86_64-unknown-linux-gnu",
        ("linux", "aarch64") => "aarch64-unknown-linux-gnu",
        ("macos", "x86_64") => "x86_64-apple-darwin",
        ("macos", "aarch64") => "aarch64-apple-darwin",
        other => panic!("no release archive is packed for {other:?}"),
    };
    format!("folio-{triple}.tar.gz")
}

/// A release archive as `release.yml` packs it: `entries` at the root, every
/// file executable.
fn archive(dir: &Path, label: &str, entries: &[(&str, &str)]) -> Vec<u8> {
    let stage = dir.join(format!("stage-{label}"));
    fs::create_dir_all(&stage).unwrap();
    for (name, content) in entries {
        let path = stage.join(name);
        fs::write(&path, content).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o755)).unwrap();
    }
    let path = dir.join(format!("release-{label}.tar.gz"));
    let mut tar = Command::new("tar");
    tar.arg("-czf").arg(&path).arg("-C").arg(&stage);
    for (name, _) in entries {
        tar.arg(name);
    }
    assert!(tar.status().expect("tar").success());
    fs::read(&path).unwrap()
}

/// The usual release: a `folio` script that answers `--version` with
/// `version`, and LICENSE.
fn folio_archive(dir: &Path, version: &str) -> Vec<u8> {
    let script = format!("#!/bin/sh\necho \"folio {version}\"\n");
    archive(
        dir,
        version,
        &[("folio", script.as_str()), ("LICENSE", "MIT\n")],
    )
}

fn sha256_hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

/// The `SHA256SUMS` line `sha256sum` writes for the archive.
fn sums(digest: &str) -> String {
    format!("{digest}  {}\n", asset())
}

/// A release `tag` served the way GitHub serves one: `latest` redirects to
/// the tag page, and every download redirects to the object store before the
/// bytes arrive. `sums` is the `SHA256SUMS` text; `None` publishes none.
fn release(tag: &str, bytes: Vec<u8>, sums: Option<String>) -> HashMap<String, Reply> {
    let mut routes = HashMap::new();
    routes.insert(
        "/releases/latest".to_string(),
        Reply::Redirect(format!("/releases/tag/{tag}")),
    );
    routes.insert(
        format!("/releases/tag/{tag}"),
        Reply::Bytes(format!("<html>folio {tag}</html>").into_bytes()),
    );
    let checksums = match sums {
        Some(text) => Reply::Bytes(text.into_bytes()),
        None => Reply::Missing,
    };
    for (name, reply) in [
        (asset(), Reply::Bytes(bytes)),
        ("SHA256SUMS".to_string(), checksums),
    ] {
        routes.insert(
            format!("/releases/download/{tag}/{name}"),
            Reply::Redirect(format!("/objects/{tag}/{name}")),
        );
        routes.insert(format!("/objects/{tag}/{name}"), reply);
    }
    routes
}

/// A copy of the built binary in its own `bin/`, the one `--update` may replace.
fn installed(dir: &Path) -> PathBuf {
    let bin = dir.join("bin");
    fs::create_dir_all(&bin).unwrap();
    let exe = bin.join("folio");
    fs::copy(env!("CARGO_BIN_EXE_folio"), &exe).unwrap();
    exe
}

/// `command` run with colours off, no proxy on the loopback, the machine's
/// repository knob cleared and, unless the caller set a server, the network
/// pointed at a closed port.
fn run(command: &mut Command) -> Run {
    if !command
        .get_envs()
        .any(|(name, _)| name == "FOLIO_RELEASES_URL")
    {
        command.env("FOLIO_RELEASES_URL", NOWHERE);
    }
    let output = command
        .env("NO_COLOR", "1")
        .env("no_proxy", "127.0.0.1")
        .env("NO_PROXY", "127.0.0.1")
        .env_remove("FOLIO_REPO")
        .output()
        .expect("folio binary");
    Run {
        code: output.status.code().unwrap_or(-1),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
    }
}

/// `exe --update` against `server`, the URL padded and slashed the way a
/// shell export can leave it.
fn update(exe: &Path, server: &ReleaseServer) -> Run {
    run(Command::new(exe)
        .arg("--update")
        .env("FOLIO_RELEASES_URL", format!("  {}/  ", server.releases)))
}

/// The step labels in order.
fn labels(run: &Run) -> Vec<&str> {
    run.rows()
        .iter()
        .map(|row| row.split_whitespace().nth(1).unwrap())
        .collect()
}

/// Everything beside the binary in its directory: staging left behind.
fn leftovers(exe: &Path) -> Vec<String> {
    fs::read_dir(exe.parent().unwrap())
        .unwrap()
        .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|name| name != "folio")
        .collect()
}

fn version_of(exe: &Path) -> String {
    let output = Command::new(exe).arg("--version").output().unwrap();
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

#[test]
fn an_up_to_date_or_newer_binary_reports_the_latest_release_and_stays() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let before = fs::read(&exe).unwrap();
    for (tag, row) in [
        (
            format!("v{VERSION}"),
            format!("folio {VERSION} is the latest release (v{VERSION})"),
        ),
        (
            "v0.0.1".to_string(),
            format!("folio {VERSION} is ahead of the latest release (v0.0.1)"),
        ),
    ] {
        let bytes = folio_archive(dir.path(), &tag);
        let digest = sha256_hex(&bytes);
        let server = ReleaseServer::start(release(&tag, bytes, Some(sums(&digest))));

        let run = update(&exe, &server);
        run.ok();
        assert_eq!(labels(&run), ["Release"], "{}", run.stdout);
        assert!(run.stdout.contains(&row), "{row:?} in\n{}", run.stdout);
        assert_eq!(fs::read(&exe).unwrap(), before);
        assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
    }
}

#[test]
fn a_newer_release_replaces_the_binary_in_place() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let bytes = folio_archive(dir.path(), "9.9.9");
    let digest = sha256_hex(&bytes);
    let server = ReleaseServer::start(release("v9.9.9", bytes, Some(sums(&digest))));

    let run = update(&exe, &server);
    run.ok();
    assert_eq!(
        labels(&run),
        ["Release", "Download", "Checksum", "Installed"],
        "{}",
        run.stdout
    );
    let rows = run.rows();
    assert!(
        rows[0].contains(&format!("v9.9.9 replaces folio {VERSION}")),
        "{}",
        rows[0]
    );
    assert!(rows[1].contains(&asset()), "{}", rows[1]);
    assert!(rows[2].contains("SHA256SUMS"), "{}", rows[2]);
    let installed_at = fs::canonicalize(&exe).unwrap();
    assert!(
        rows[3].contains("folio 9.9.9") && rows[3].contains(&installed_at.display().to_string()),
        "{}",
        rows[3]
    );
    assert_eq!(version_of(&exe), "folio 9.9.9");
    assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
}

#[test]
fn a_release_that_cannot_be_trusted_or_run_leaves_the_binary_alone() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let before = fs::read(&exe).unwrap();
    let good = folio_archive(dir.path(), "9.9.9");
    let wrong = sha256_hex(b"another archive");
    let no_binary = archive(dir.path(), "license-only", &[("LICENSE", "MIT\n")]);
    let broken = archive(
        dir.path(),
        "broken",
        &[("folio", "#!/bin/sh\nexit 3\n"), ("LICENSE", "MIT\n")],
    );
    let cases: [(&[u8], Option<String>, &str); 5] = [
        (&good, Some(sums(&wrong)), "does not match SHA256SUMS"),
        (
            &good,
            Some(format!("{wrong}  folio-other.tar.gz\n")),
            "does not name",
        ),
        (&good, None, "publishes no SHA256SUMS"),
        (
            &no_binary,
            Some(sums(&sha256_hex(&no_binary))),
            "did not contain a folio binary",
        ),
        (
            &broken,
            Some(sums(&sha256_hex(&broken))),
            "does not start here",
        ),
    ];
    for (bytes, sums, message) in cases {
        let server = ReleaseServer::start(release("v9.9.9", bytes.to_vec(), sums));
        let run = update(&exe, &server);
        let reported = run.diagnostics();
        assert_eq!(run.code, 1, "{reported}");
        assert!(
            reported.contains("Error:") && reported.contains(message),
            "{message:?} in\n{reported}"
        );
        assert_eq!(fs::read(&exe).unwrap(), before, "{message}");
        assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
    }
}

#[test]
fn a_repository_without_releases_or_without_a_page_is_one_clear_error() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let before = fs::read(&exe).unwrap();

    // No release yet: `latest` lands on the releases page itself.
    let mut routes = HashMap::new();
    routes.insert(
        "/releases/latest".to_string(),
        Reply::Redirect("/releases".to_string()),
    );
    routes.insert(
        "/releases".to_string(),
        Reply::Bytes(b"<html>no releases</html>".to_vec()),
    );
    let server = ReleaseServer::start(routes);
    let run = update(&exe, &server);
    let reported = run.diagnostics();
    assert_eq!(run.code, 1, "{reported}");
    assert!(
        reported.contains(&format!(
            "Error: no release is published yet at {}",
            server.releases
        )),
        "{reported}"
    );

    // An unknown repository: `latest` is a 404, and the error still says where to look.
    let server = ReleaseServer::start(HashMap::new());
    let run = update(&exe, &server);
    let reported = run.diagnostics();
    assert_eq!(run.code, 1, "{reported}");
    assert!(
        reported.contains("/releases/latest")
            && reported.contains(&format!("see {}", server.releases)),
        "{reported}"
    );

    assert_eq!(fs::read(&exe).unwrap(), before);
    assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
}

#[test]
fn a_directory_the_user_cannot_write_to_stops_before_the_download() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let before = fs::read(&exe).unwrap();
    let bin = exe.parent().unwrap().to_path_buf();
    let bytes = folio_archive(dir.path(), "9.9.9");
    let digest = sha256_hex(&bytes);
    let server = ReleaseServer::start(release("v9.9.9", bytes, Some(sums(&digest))));

    /// The directory is writable again when the test ends, panic or not, so
    /// the tempdir can be removed.
    struct Writable(PathBuf);
    impl Drop for Writable {
        fn drop(&mut self) {
            let _ = fs::set_permissions(&self.0, fs::Permissions::from_mode(0o755));
        }
    }
    let _restore = Writable(bin.clone());
    fs::set_permissions(&bin, fs::Permissions::from_mode(0o555)).unwrap();
    let still_writable = fs::write(bin.join(".probe"), b"").is_ok();
    let run = update(&exe, &server);
    if still_writable {
        fs::set_permissions(&bin, fs::Permissions::from_mode(0o755)).unwrap();
        let _ = fs::remove_file(bin.join(".probe"));
        eprintln!("skipped: the directory stays writable, this user ignores modes");
        return;
    }
    let reported = run.diagnostics();
    assert_eq!(run.code, 1, "{reported}");
    assert_eq!(labels(&run), ["Release"], "{}", run.stdout);
    assert!(
        reported.contains("cannot write to") && reported.contains("Re-run with write access"),
        "{reported}"
    );
    assert_eq!(fs::read(&exe).unwrap(), before);
    assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
}

#[test]
fn update_runs_alone() {
    let dir = tempfile::tempdir().unwrap();
    let exe = installed(dir.path());
    let before = fs::read(&exe).unwrap();
    let bytes = folio_archive(dir.path(), "9.9.9");
    let digest = sha256_hex(&bytes);
    let server = ReleaseServer::start(release("v9.9.9", bytes, Some(sums(&digest))));

    let run = run(Command::new(&exe)
        .args(["--update", "build"])
        .env("FOLIO_RELEASES_URL", &server.releases));
    assert_eq!(run.code, 2, "{}", run.stdout);
    assert!(
        run.stderr.contains("--update") && run.stderr.contains("build"),
        "{}",
        run.stderr
    );
    assert_eq!(
        fs::read(&exe).unwrap(),
        before,
        "a usage error touches nothing"
    );
    assert!(leftovers(&exe).is_empty(), "{:?}", leftovers(&exe));
}
