use super::*;

#[test]
fn the_release_asset_is_named_as_release_yml_packs_it() {
    for (os, arch, asset) in [
        ("linux", "x86_64", "folio-x86_64-unknown-linux-gnu.tar.gz"),
        ("linux", "aarch64", "folio-aarch64-unknown-linux-gnu.tar.gz"),
        ("macos", "x86_64", "folio-x86_64-apple-darwin.tar.gz"),
        ("macos", "aarch64", "folio-aarch64-apple-darwin.tar.gz"),
        ("windows", "x86_64", "folio-x86_64-pc-windows-msvc.zip"),
    ] {
        assert_eq!(release_asset(os, arch).as_deref(), Some(asset));
    }
    for (os, arch) in [
        ("linux", "arm"),
        ("windows", "aarch64"),
        ("freebsd", "x86_64"),
    ] {
        assert_eq!(release_asset(os, arch), None, "{os}-{arch}");
    }
}

#[test]
fn the_tag_is_where_the_latest_release_page_lands() {
    const GITHUB: &str = "https://github.com/pguijas/folio/releases";
    const MIRROR: &str = "http://mirror.test/folio";
    for (url, releases, tag) in [
        (
            "https://github.com/pguijas/folio/releases/tag/v0.3.1",
            GITHUB,
            Some("v0.3.1"),
        ),
        (
            "https://github.com/pguijas/folio/releases/tag/v0.3.1/",
            GITHUB,
            Some("v0.3.1"),
        ),
        (
            "http://127.0.0.1:4000/releases/tag/v9.9.9?from=latest",
            "http://127.0.0.1:4000/releases",
            Some("v9.9.9"),
        ),
        // A mirror base without `/releases` in it: the tag follows the base.
        (
            "http://mirror.test/folio/tag/v0.4.0",
            MIRROR,
            Some("v0.4.0"),
        ),
        (
            "http://mirror.test/folio/tag/v0.4.0",
            "http://mirror.test/folio/",
            Some("v0.4.0"),
        ),
        // A mirror that redirects back to GitHub: the marker still finds the tag.
        (
            "https://github.com/pguijas/folio/releases/tag/v0.4.0",
            MIRROR,
            Some("v0.4.0"),
        ),
        ("https://github.com/pguijas/folio/releases", GITHUB, None),
        (
            "https://github.com/pguijas/folio/releases/tag/",
            GITHUB,
            None,
        ),
        ("http://mirror.test/folio", MIRROR, None),
        ("", GITHUB, None),
    ] {
        assert_eq!(tag_from_url(url, releases), tag, "{url} under {releases}");
    }
}

#[test]
fn tags_compare_as_cargo_versions_with_or_without_the_v() {
    assert_eq!(parse_version("v0.3.1").unwrap(), Version::new(0, 3, 1));
    assert_eq!(parse_version("0.3.1").unwrap(), Version::new(0, 3, 1));
    assert!(
        parse_version("v0.3.0-a1").unwrap() < Version::new(0, 3, 0),
        "a prerelease precedes its release"
    );
    assert!(
        parse_version(CURRENT).is_ok(),
        "the compiled-in version parses"
    );
    assert!(
        parse_version("v0.3.0-a10").unwrap() > parse_version("v0.3.0-a9").unwrap(),
        "a10 follows a9: the number counts as a number"
    );
    assert!(parse_version("v0.3.0-a2").unwrap() < parse_version("v0.3.0-b1").unwrap());
    assert!(parse_version("v0.3.0-rc1").unwrap() < parse_version("v0.3.0").unwrap());
    assert_eq!(
        parse_version("v0.3.0-a1").unwrap(),
        parse_version("0.3.0-a1").unwrap()
    );
    let error = parse_version("nightly").unwrap_err().to_string();
    assert!(
        error.contains("nightly") && error.contains("not a version"),
        "{error}"
    );
}

#[test]
fn the_checksum_line_for_the_asset_is_found_in_either_sums_format() {
    let plain = "a".repeat(64);
    let binary = "B".repeat(64);
    let relative = "c".repeat(64);
    let sums = format!(
        "{plain}  folio-x86_64-apple-darwin.tar.gz\n\
         {binary} *folio-x86_64-pc-windows-msvc.zip\n\
         {relative}  ./folio-aarch64-unknown-linux-gnu.tar.gz\n\
         {relative}  folio-x86_64-apple-darwin.tar.gz.sig\n\
         short  folio-aarch64-apple-darwin.tar.gz\n\n"
    );
    assert_eq!(
        checksum_for(&sums, "folio-x86_64-apple-darwin.tar.gz").as_deref(),
        Some(plain.as_str()),
        "the exact name, not its .sig neighbour"
    );
    assert_eq!(
        checksum_for(&sums, "folio-aarch64-unknown-linux-gnu.tar.gz").as_deref(),
        Some(relative.as_str()),
        "a ./ prefix on the name"
    );
    assert_eq!(
        checksum_for(&sums, "folio-x86_64-pc-windows-msvc.zip"),
        Some(binary.to_ascii_lowercase())
    );
    assert_eq!(
        checksum_for(&sums, "folio-aarch64-apple-darwin.tar.gz"),
        None,
        "a malformed digest is no digest"
    );
    assert_eq!(
        checksum_for(&sums, "folio-x86_64-unknown-linux-gnu.tar.gz"),
        None
    );
}

#[test]
fn replace_puts_the_fresh_binary_at_the_old_ones_path() {
    let dir = tempfile::tempdir().unwrap();
    let exe = dir.path().join(BINARY);
    let fresh = dir.path().join("fresh");
    fs::write(&exe, b"old").unwrap();
    fs::write(&fresh, b"new").unwrap();
    replace(&fresh, &exe).unwrap();
    assert_eq!(fs::read(&exe).unwrap(), b"new");
    assert!(!fresh.exists(), "the fresh file moved, it was not copied");
    #[cfg(windows)]
    assert_eq!(
        fs::read(exe.with_extension("exe.old")).unwrap(),
        b"old",
        "the previous binary stays beside the new one"
    );
}

#[test]
fn the_releases_url_is_the_override_or_the_repositorys_page() {
    assert_eq!(
        releases_url_from(None, None),
        "https://github.com/pguijas/folio/releases"
    );
    assert_eq!(
        releases_url_from(None, Some("me/fork")),
        "https://github.com/me/fork/releases"
    );
    assert_eq!(
        releases_url_from(Some("http://mirror.test/folio/releases/"), Some("me/fork")),
        "http://mirror.test/folio/releases"
    );
}
