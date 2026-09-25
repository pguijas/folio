use super::*;

#[test]
fn urlsplit_matches_python() {
    assert_eq!(
        urlsplit("https://example.com/docs/?a=1#f"),
        (
            "https".into(),
            "example.com".into(),
            "/docs/".into(),
            "a=1".into(),
            "f".into()
        )
    );
    assert_eq!(
        urlsplit("/docs/components"),
        (
            "".into(),
            "".into(),
            "/docs/components".into(),
            "".into(),
            "".into()
        )
    );
    assert_eq!(
        urlsplit("//cdn/x.js"),
        (
            "".into(),
            "cdn".into(),
            "/x.js".into(),
            "".into(),
            "".into()
        )
    );
    assert_eq!(
        urlsplit("mailto:a@b"),
        (
            "mailto".into(),
            "".into(),
            "a@b".into(),
            "".into(),
            "".into()
        )
    );
    assert_eq!(
        urlsplit("#local"),
        ("".into(), "".into(), "".into(), "".into(), "local".into())
    );
    assert_eq!(
        urlsplit("./c#frag"),
        ("".into(), "".into(), "./c".into(), "".into(), "frag".into())
    );
}

#[test]
fn relpath_matches_os_path_relpath() {
    assert_eq!(
        relpath(Path::new("/o/index.html"), Path::new("/o/docs")),
        "../index.html"
    );
    assert_eq!(
        relpath(Path::new("/o/docs/index.html"), Path::new("/o/docs")),
        "index.html"
    );
    assert_eq!(relpath(Path::new("/o/docs"), Path::new("/o/docs")), ".");
    assert_eq!(
        relpath(Path::new("/o/_next/a.js"), Path::new("/o")),
        "_next/a.js"
    );
}

#[test]
fn opengraph_image_urls_gain_png() {
    let text = "a=\"https://x/docs/opengraph-image?abc\" b=\"/opengraph-image\" c=\"opengraph-image.png\" d=opengraph-image.tsx e=\\\"x/opengraph-image\\\"";
    assert_eq!(
            StaticAssetRewriter::rewrite_opengraph_image_urls(text),
            "a=\"https://x/docs/opengraph-image.png?abc\" b=\"/opengraph-image.png\" c=\"opengraph-image.png\" d=opengraph-image.tsx e=\\\"x/opengraph-image.png\\\""
        );
    assert_eq!(
        StaticAssetRewriter::rewrite_opengraph_image_urls("end opengraph-image"),
        "end opengraph-image.png"
    );
}
