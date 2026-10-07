use super::*;

#[test]
fn paths_resolve_inside_the_site_with_index_and_redirects() {
    let dir = tempfile::tempdir().unwrap();
    let site = dir.path();
    std::fs::create_dir_all(site.join("docs/guide")).unwrap();
    std::fs::write(site.join("index.html"), "root").unwrap();
    std::fs::write(site.join("docs/guide/index.html"), "guide").unwrap();
    std::fs::write(site.join("docs/a b.css"), "css").unwrap();
    assert_eq!(
        resolve(site, "/"),
        Resolution::File(site.join("index.html"))
    );
    assert_eq!(
        resolve(site, "/docs/guide/?x=1"),
        Resolution::File(site.join("docs/guide/index.html"))
    );
    assert_eq!(
        resolve(site, "/docs/guide"),
        Resolution::Redirect("/docs/guide/".to_string())
    );
    assert_eq!(
        resolve(site, "/docs/a%20b.css"),
        Resolution::File(site.join("docs/a b.css"))
    );
    assert_eq!(resolve(site, "/missing/"), Resolution::NotFound);
    assert_eq!(resolve(site, "/%aé"), Resolution::NotFound);
    assert_eq!(percent_decode("/%aé%2"), "/%aé%2");
    assert_eq!(percent_decode("/caf%C3%A9"), "/café");
    assert_eq!(resolve(site, "/../etc/passwd"), Resolution::NotFound);
    assert_eq!(
        resolve(site, "/docs"),
        Resolution::Redirect("/docs/".to_string())
    );
    assert_eq!(mime_type(Path::new("x.html")), "text/html; charset=utf-8");
    assert_eq!(mime_type(Path::new("x.bin")), "application/octet-stream");
}
