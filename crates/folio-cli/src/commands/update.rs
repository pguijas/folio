//! `folio --update`: replace the running binary with the latest GitHub
//! release, the way `install.sh` installs it. `curl` follows the redirect of
//! `releases/latest` to learn the tag and downloads the archive; `SHA256SUMS`
//! from the same release must name the archive's digest; `tar` unpacks it
//! beside the binary; the new file takes the old one's path. The tools are
//! the installer's, so the binary gains no TLS stack.

use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;

use semver::{Prerelease, Version};

use crate::error::CliError;
use crate::ui::steps::step;
use crate::ui::text::{BOLD, GREEN};
use crate::ui::Ui;

/// The compiled-in version, what `--version` prints.
const CURRENT: &str = env!("CARGO_PKG_VERSION");
/// The repository `install.sh` downloads from unless `FOLIO_REPO` says otherwise.
const DEFAULT_REPO: &str = "pguijas/folio";
/// The checksum file `release.yml` publishes next to the archives.
const SUMS: &str = "SHA256SUMS";
/// The binary at the archive root.
const BINARY: &str = if cfg!(windows) { "folio.exe" } else { "folio" };
/// Where curl drops a page whose only interest is the URL it lands on.
const SINK: &str = if cfg!(windows) { "NUL" } else { "/dev/null" };

/// `✓ Label › detail`: the row the pipeline prints for a finished step, here
/// for a command that has no pipeline reporter behind it.
fn step_ok(ui: &Ui, label: &str, detail: &str) {
    step(ui, label, detail, "✓", GREEN, BOLD);
}

/// Resolve the latest release and, when it is newer than this binary,
/// download, verify, unpack and swap it in place. An up-to-date binary
/// reports so and changes nothing.
pub fn run(ui: &Ui) -> Result<(), CliError> {
    let releases = releases_url();
    let asset = release_asset(env::consts::OS, env::consts::ARCH).ok_or_else(|| {
        CliError::message(format!(
            "no release archive is published for {}-{}; see {releases}",
            env::consts::OS,
            env::consts::ARCH
        ))
    })?;
    let exe = fs::canonicalize(env::current_exe()?)?;

    let landed = fetch(&format!("{releases}/latest"), None)
        .map_err(|err| CliError::message(format!("{err}; see {releases}")))?;
    let tag = tag_from_url(landed.trim(), &releases)
        .ok_or_else(|| CliError::message(format!("no release is published yet at {releases}")))?
        .to_string();
    let latest = parse_version(&tag)?;
    let current = parse_version(CURRENT)?;
    if latest == current {
        step_ok(
            ui,
            "Release",
            &format!("folio {CURRENT} is the latest release ({tag})"),
        );
        return Ok(());
    }
    if latest < current {
        step_ok(
            ui,
            "Release",
            &format!("folio {CURRENT} is ahead of the latest release ({tag})"),
        );
        return Ok(());
    }
    step_ok(ui, "Release", &format!("{tag} replaces folio {CURRENT}"));

    let staging = Staging::beside(&exe)?;
    let download = format!("{releases}/download/{tag}");
    let archive = staging.dir.join(&asset);
    fetch(&format!("{download}/{asset}"), Some(&archive))
        .map_err(|err| CliError::message(format!("{err}; see {releases}")))?;
    step_ok(ui, "Download", &asset);

    let sums_file = staging.dir.join(SUMS);
    fetch(&format!("{download}/{SUMS}"), Some(&sums_file)).map_err(|err| {
        if err.contains("404") {
            CliError::message(format!(
                "{tag} publishes no {SUMS}, so {asset} cannot be verified ({err})"
            ))
        } else {
            CliError::message(format!("{err}; see {releases}"))
        }
    })?;
    let expected = checksum_for(&fs::read_to_string(&sums_file)?, &asset)
        .ok_or_else(|| CliError::message(format!("{SUMS} of {tag} does not name {asset}")))?;
    let actual = folio_site::fs::sha256_hex(&fs::read(&archive)?);
    if actual != expected {
        return Err(CliError::message(format!(
            "{asset} does not match {SUMS}: expected {expected}, got {actual}"
        )));
    }
    step_ok(ui, "Checksum", &format!("{SUMS} names {asset}"));

    extract(&archive, &staging.dir)?;
    let fresh = staging.dir.join(BINARY);
    let regular = fs::symlink_metadata(&fresh).is_ok_and(|meta| meta.file_type().is_file());
    if !regular {
        return Err(CliError::message(format!(
            "{asset} did not contain a {BINARY} binary"
        )));
    }
    make_executable(&fresh)?;
    let reported = version_of(&fresh)?;
    replace(&fresh, &exe)?;
    step_ok(ui, "Installed", &format!("{reported} at {}", exe.display()));
    Ok(())
}

/// `FOLIO_RELEASES_URL` (a mirror or a test server) or GitHub's releases
/// page for `FOLIO_REPO`, the installer's knob; empty values count as unset.
fn releases_url() -> String {
    releases_url_from(
        env_non_empty("FOLIO_RELEASES_URL").as_deref(),
        env_non_empty("FOLIO_REPO").as_deref(),
    )
}

fn releases_url_from(override_url: Option<&str>, repo: Option<&str>) -> String {
    match override_url {
        Some(url) => url.trim_end_matches('/').to_string(),
        None => format!(
            "https://github.com/{}/releases",
            repo.unwrap_or(DEFAULT_REPO)
        ),
    }
}

fn env_non_empty(name: &str) -> Option<String> {
    env::var(name)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
}

/// The archive `release.yml` packs for this platform, named as `install.sh`
/// composes it from `uname`: `.tar.gz` everywhere, `.zip` on Windows.
fn release_asset(os: &str, arch: &str) -> Option<String> {
    let triple = match (os, arch) {
        ("linux", "x86_64") => "x86_64-unknown-linux-gnu",
        ("linux", "aarch64") => "aarch64-unknown-linux-gnu",
        ("macos", "x86_64") => "x86_64-apple-darwin",
        ("macos", "aarch64") => "aarch64-apple-darwin",
        ("windows", "x86_64") => "x86_64-pc-windows-msvc",
        _ => return None,
    };
    let extension = if os == "windows" { "zip" } else { "tar.gz" };
    Some(format!("folio-{triple}.{extension}"))
}

/// The tag in `<releases>/tag/<tag>`, where `<releases>/latest` lands. GitHub
/// keeps `/releases/tag/` in the path, so that marker is the fallback for a
/// mirror that redirects back to GitHub. A repository without releases lands
/// on `<releases>` itself and yields nothing.
fn tag_from_url<'a>(url: &'a str, releases: &str) -> Option<&'a str> {
    const MARKER: &str = "/releases/tag/";
    let base = format!("{}/tag/", releases.trim_end_matches('/'));
    let rest = url
        .strip_prefix(base.as_str())
        .or_else(|| url.find(MARKER).map(|at| &url[at + MARKER.len()..]))?;
    let tag = rest.split(['/', '?', '#']).next().unwrap_or("");
    (!tag.is_empty()).then_some(tag)
}

/// A release tag as a Cargo version, with or without the leading `v`, its
/// prerelease shaped so that versions compare in release order.
fn parse_version(tag: &str) -> Result<Version, CliError> {
    let tag = tag.trim();
    let bare = tag
        .strip_prefix('v')
        .or_else(|| tag.strip_prefix('V'))
        .unwrap_or(tag);
    let mut version = Version::parse(bare)
        .map_err(|err| CliError::message(format!("release tag {tag} is not a version: {err}")))?;
    version.pre = comparable_prerelease(&version.pre);
    Ok(version)
}

/// Semver compares an alphanumeric identifier letter by letter, so `a10`
/// sorts before `a9`. Folio's PEP 440-shaped prereleases (`a1`, `b2`, `rc3`)
/// split into `a.1`, where the number counts as a number. Anything else stays.
fn comparable_prerelease(pre: &Prerelease) -> Prerelease {
    if pre.is_empty() {
        return pre.clone();
    }
    let split: Vec<String> = pre
        .as_str()
        .split('.')
        .map(|id| {
            let digits = id.trim_start_matches(|c: char| c.is_ascii_alphabetic());
            let letters = &id[..id.len() - digits.len()];
            if !letters.is_empty()
                && !digits.is_empty()
                && digits.bytes().all(|b| b.is_ascii_digit())
            {
                format!("{letters}.{digits}")
            } else {
                id.to_string()
            }
        })
        .collect();
    Prerelease::new(&split.join(".")).unwrap_or_else(|_| pre.clone())
}

/// The digest `SHA256SUMS` records for `asset`: `<hex>  <name>` lines, the
/// name possibly marked binary (`*name`) or relative (`./name`).
fn checksum_for(sums: &str, asset: &str) -> Option<String> {
    sums.lines().find_map(|line| {
        let mut parts = line.split_whitespace();
        let digest = parts.next()?;
        let name = parts
            .next()?
            .trim_start_matches('*')
            .trim_start_matches("./");
        let well_formed = digest.len() == 64 && digest.chars().all(|c| c.is_ascii_hexdigit());
        (name == asset && well_formed).then(|| digest.to_ascii_lowercase())
    })
}

/// `curl -fsSL` on `url`: saved to `save_to`, or discarded with the URL it
/// finally landed on as the result. `-g` keeps IPv6 literals whole, `--url`
/// keeps a URL from being read as an option, and a transfer that stalls for
/// a minute ends instead of hanging. The error names the URL and curl's report.
fn fetch(url: &str, save_to: Option<&Path>) -> Result<String, String> {
    let mut curl = Command::new("curl");
    curl.args(["-fsSL", "-g", "--connect-timeout", "15"]);
    curl.args(["--speed-limit", "1", "--speed-time", "60", "-o"]);
    match save_to {
        Some(path) => curl.arg(path),
        None => curl.args([SINK, "-w", "%{url_effective}"]),
    };
    let output = curl
        .arg("--url")
        .arg(url)
        .output()
        .map_err(|err| match err.kind() {
            io::ErrorKind::NotFound => "curl is not installed and --update needs it".to_string(),
            _ => format!("curl: {err}"),
        })?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(format!(
            "{url}: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ))
    }
}

/// A directory beside the binary, on its filesystem, so the final rename is
/// atomic; it holds the download until it is installed and goes when dropped.
struct Staging {
    dir: PathBuf,
}

impl Staging {
    fn beside(exe: &Path) -> Result<Staging, CliError> {
        let parent = exe.parent().ok_or_else(|| {
            CliError::message(format!("{} has no parent directory", exe.display()))
        })?;
        let dir = parent.join(format!(".folio-update-{}", std::process::id()));
        fs::create_dir_all(&dir).map_err(|err| {
            CliError::message(format!(
                "cannot write to {}: {err}. Re-run with write access to it or use the installer",
                parent.display()
            ))
        })?;
        Ok(Staging { dir })
    }
}

impl Drop for Staging {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.dir);
    }
}

/// `tar -xf archive -C dir`: gzip and zip alike, the way the installer unpacks.
fn extract(archive: &Path, dir: &Path) -> Result<(), CliError> {
    let output = Command::new("tar")
        .arg("-xf")
        .arg(archive)
        .arg("-C")
        .arg(dir)
        .output()
        .map_err(|err| match err.kind() {
            io::ErrorKind::NotFound => CliError::message(
                "tar is not installed and --update needs it to unpack the release",
            ),
            _ => CliError::message(format!("tar: {err}")),
        })?;
    if output.status.success() {
        Ok(())
    } else {
        Err(CliError::message(format!(
            "tar could not unpack {}: {}",
            archive.display(),
            String::from_utf8_lossy(&output.stderr).trim()
        )))
    }
}

#[cfg(unix)]
fn make_executable(path: &Path) -> Result<(), CliError> {
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(path, fs::Permissions::from_mode(0o755))?;
    Ok(())
}

#[cfg(not(unix))]
fn make_executable(_path: &Path) -> Result<(), CliError> {
    Ok(())
}

/// `<fresh> --version`: the downloaded binary runs on this machine and says
/// which version it is, before it replaces anything.
fn version_of(fresh: &Path) -> Result<String, CliError> {
    let output = Command::new(fresh)
        .arg("--version")
        .output()
        .map_err(|err| {
            CliError::message(format!("the downloaded binary does not start here: {err}"))
        })?;
    if !output.status.success() {
        return Err(CliError::message(format!(
            "the downloaded binary does not start here ({}): {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// The new binary takes the old one's path. A rename over a running
/// executable is atomic on Unix.
#[cfg(unix)]
fn replace(fresh: &Path, exe: &Path) -> Result<(), CliError> {
    fs::rename(fresh, exe)
        .map_err(|err| CliError::message(format!("cannot replace {}: {err}", exe.display())))
}

/// Windows keeps a running executable locked against overwrite but not
/// against rename: the old binary moves aside as `.exe.old`, the new one
/// takes its path. When the second rename fails the old one comes back, or
/// the error says where it is.
#[cfg(not(unix))]
fn replace(fresh: &Path, exe: &Path) -> Result<(), CliError> {
    let aside = exe.with_extension("exe.old");
    let _ = fs::remove_file(&aside);
    fs::rename(exe, &aside)
        .map_err(|err| CliError::message(format!("cannot move {} aside: {err}", exe.display())))?;
    if let Err(err) = fs::rename(fresh, exe) {
        return Err(match fs::rename(&aside, exe) {
            Ok(()) => CliError::message(format!(
                "cannot replace {}: {err}; the previous binary is back in place",
                exe.display()
            )),
            Err(back) => CliError::message(format!(
                "cannot replace {}: {err}; the previous binary is at {} ({back})",
                exe.display(),
                aside.display()
            )),
        });
    }
    Ok(())
}

#[cfg(test)]
#[path = "update_tests.rs"]
mod tests;
