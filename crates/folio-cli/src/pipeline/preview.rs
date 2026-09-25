//! The static preview server behind `folio build --open` and
//! `folio serve --versions`: a
//! `std::net` file server over the exported site that moves to the next free
//! port, serves `index.html` for directories, redirects a directory without
//! its trailing `/`, and answers 404 otherwise. No listing, no base path.

use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::Duration;

use folio_site::runtime::{is_port_in_use, kill_port};

use crate::ui::text::{BOLD_CYAN, DIM, GREEN};
use crate::ui::Ui;

/// Serve `site_dir` on `port` (or the next free one) until interrupted.
pub fn serve_static_site(
    ui: &Ui,
    site_dir: &Path,
    mut port: u16,
    open_browser: bool,
    kill_existing: bool,
) -> std::io::Result<()> {
    if kill_existing {
        kill_port(port);
    }
    while is_port_in_use(port) {
        port += 1;
    }
    let listener = TcpListener::bind(("127.0.0.1", port))?;
    let url = format!("http://localhost:{port}");
    ui.blank();
    ui.print(&format!(
        "{} {}",
        ui.styled(GREEN, "Serving site at"),
        ui.styled(BOLD_CYAN, &url)
    ));
    ui.print_styled(DIM, "Press Ctrl+C to stop");
    ui.blank();
    if open_browser {
        open_in_browser(&url);
    }
    // One thread per connection: served serially, a browser holding a
    // keep-alive socket open blocked every other request.
    // ponytail: unbounded threads, a pool if a preview ever serves a crowd.
    let root = site_dir.to_path_buf();
    for stream in listener.incoming().flatten() {
        let root = root.clone();
        thread::spawn(move || {
            // A client that opens a socket and says nothing releases it.
            let _ = stream.set_read_timeout(Some(Duration::from_secs(10)));
            let _ = stream.set_write_timeout(Some(Duration::from_secs(30)));
            let _ = handle(stream, &root);
        });
    }
    Ok(())
}

/// Open `url` with the platform opener; failures are ignored.
pub fn open_in_browser(url: &str) {
    #[cfg(target_os = "macos")]
    let mut command = {
        let mut c = Command::new("open");
        c.arg(url);
        c
    };
    #[cfg(target_os = "windows")]
    let mut command = {
        let mut c = Command::new("cmd");
        c.args(["/c", "start", "", url]);
        c
    };
    #[cfg(not(any(target_os = "macos", target_os = "windows")))]
    let mut command = {
        let mut c = Command::new("xdg-open");
        c.arg(url);
        c
    };
    let _ = command
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn();
}

/// What one request resolves to.
#[derive(Debug, PartialEq, Eq)]
pub enum Resolution {
    File(PathBuf),
    /// The directory exists but the path lacks its trailing `/`.
    Redirect(String),
    NotFound,
}

/// Map a request path onto `site_dir`; `..` never escapes it.
pub fn resolve(site_dir: &Path, request_path: &str) -> Resolution {
    let path = request_path.split(['?', '#']).next().unwrap_or("");
    let decoded = percent_decode(path);
    let mut target = site_dir.to_path_buf();
    for part in Path::new(&decoded).components() {
        match part {
            Component::Normal(name) => target.push(name),
            Component::ParentDir => return Resolution::NotFound,
            _ => {}
        }
    }
    if target.is_dir() {
        if !decoded.ends_with('/') {
            return Resolution::Redirect(format!("{decoded}/"));
        }
        target.push("index.html");
    }
    if target.is_file() {
        Resolution::File(target)
    } else {
        Resolution::NotFound
    }
}

fn percent_decode(text: &str) -> String {
    let bytes = text.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            // Bytes, not chars: `%aé` must not slice inside the `é`.
            let hex = std::str::from_utf8(&bytes[i + 1..i + 3]).ok();
            if let Some(value) = hex.and_then(|h| u8::from_str_radix(h, 16).ok()) {
                out.push(value);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

/// A small extension table; `application/octet-stream` otherwise.
pub fn mime_type(path: &Path) -> &'static str {
    match path
        .extension()
        .and_then(|e| e.to_str())
        .map(str::to_ascii_lowercase)
        .as_deref()
    {
        Some("html" | "htm") => "text/html; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("js" | "mjs") => "text/javascript; charset=utf-8",
        Some("json") => "application/json",
        Some("xml") => "application/xml",
        Some("txt" | "md") => "text/plain; charset=utf-8",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("jpg" | "jpeg") => "image/jpeg",
        Some("gif") => "image/gif",
        Some("webp") => "image/webp",
        Some("ico") => "image/x-icon",
        Some("woff") => "font/woff",
        Some("woff2") => "font/woff2",
        Some("wasm") => "application/wasm",
        _ => "application/octet-stream",
    }
}

fn handle(mut stream: TcpStream, site_dir: &Path) -> std::io::Result<()> {
    let mut reader = BufReader::new(stream.try_clone()?);
    let mut request_line = String::new();
    reader.read_line(&mut request_line)?;
    // Drain the headers; nothing in them changes the answer.
    let mut header = String::new();
    while reader.read_line(&mut header)? > 0 && !header.trim().is_empty() {
        header.clear();
    }
    let mut parts = request_line.split_whitespace();
    let method = parts.next().unwrap_or("");
    let path = parts.next().unwrap_or("/");
    if method != "GET" && method != "HEAD" {
        return respond(
            &mut stream,
            "405 Method Not Allowed",
            "text/plain",
            b"",
            &[],
        );
    }
    match resolve(site_dir, path) {
        Resolution::File(file) => {
            let mut body = Vec::new();
            std::fs::File::open(&file)?.read_to_end(&mut body)?;
            let body: &[u8] = if method == "HEAD" { b"" } else { &body };
            respond(&mut stream, "200 OK", mime_type(&file), body, &[])
        }
        Resolution::Redirect(location) => respond(
            &mut stream,
            "301 Moved Permanently",
            "text/plain",
            b"",
            &[("Location", &location)],
        ),
        Resolution::NotFound => respond(
            &mut stream,
            "404 Not Found",
            "text/plain; charset=utf-8",
            b"Not Found",
            &[],
        ),
    }
}

fn respond(
    stream: &mut TcpStream,
    status: &str,
    content_type: &str,
    body: &[u8],
    extra: &[(&str, &str)],
) -> std::io::Result<()> {
    let mut head = format!(
        "HTTP/1.0 {status}\r\nContent-Type: {content_type}\r\nContent-Length: {}\r\nConnection: close\r\n",
        body.len()
    );
    for (name, value) in extra {
        head.push_str(&format!("{name}: {value}\r\n"));
    }
    head.push_str("\r\n");
    stream.write_all(head.as_bytes())?;
    stream.write_all(body)?;
    stream.flush()
}

#[cfg(test)]
#[path = "preview_tests.rs"]
mod tests;
