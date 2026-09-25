use super::*;

#[test]
fn version_parsing_and_minimums() {
    assert_eq!(parse_version("v20.19.1-rc+x"), [20, 19, 1]);
    assert_eq!(parse_version("10.28.2"), [10, 28, 2]);
    assert_eq!(parse_version("garbage"), Vec::<u32>::new());
    assert!(too_old(&[20, 18, 9], MIN_NODE_VERSION));
    assert!(!too_old(&[20, 19], MIN_NODE_VERSION));
    assert!(!too_old(&[], MIN_NODE_VERSION));
    assert!(too_old(&[9, 15], MIN_PNPM_VERSION));
}

#[test]
fn preflight_names_every_missing_tool() {
    let err = preflight_check_with("folio-no-such-node", "folio-no-such-pnpm")
        .unwrap_err()
        .to_string();
    assert_eq!(
            err,
            "Environment check failed:\n  - Node.js was not found. The generated site is a Next.js app; install Node >= 20.19 from https://nodejs.org/\n  - pnpm was not found. Install it with: npm install -g pnpm"
        );
}

#[test]
fn occupied_port_is_detected() {
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    assert!(is_port_in_use(port));
    drop(listener);
}

/// Not a test: the listening server `kill_port_spares_the_clients` starts by
/// re-running this binary. It prints its port and waits to be killed.
#[cfg(unix)]
#[test]
#[ignore = "helper process for kill_port_spares_the_clients"]
fn listening_helper() {
    if std::env::var_os("FOLIO_TEST_LISTEN").is_none() {
        return;
    }
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    println!("FOLIO_TEST_PORT={}", listener.local_addr().unwrap().port());
    std::io::stdout().flush().unwrap();
    std::thread::sleep(Duration::from_secs(60));
}

#[cfg(unix)]
#[test]
fn kill_port_spares_the_clients() {
    use std::io::BufRead;
    use std::os::unix::process::ExitStatusExt;

    if Command::new("lsof").arg("-v").output().is_err() {
        eprintln!("lsof not found; skipping");
        return;
    }
    struct Reap(Child);
    impl Drop for Reap {
        fn drop(&mut self) {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
    let mut server = Reap(
        Command::new(std::env::current_exe().unwrap())
            .args([
                "runtime::tests::listening_helper",
                "--exact",
                "--ignored",
                "--nocapture",
            ])
            .env("FOLIO_TEST_LISTEN", "1")
            .stdout(Stdio::piped())
            .spawn()
            .unwrap(),
    );
    let stdout = server.0.stdout.take().unwrap();
    let port: u16 = std::io::BufReader::new(stdout)
        .lines()
        .map_while(std::result::Result::ok)
        .find_map(|line| line.strip_prefix("FOLIO_TEST_PORT=").map(str::to_string))
        .expect("the helper prints its port")
        .parse()
        .unwrap();
    // This process is now a client of the port: the old `lsof -ti :port`
    // listed it and SIGKILLed the test itself.
    let client = TcpStream::connect(("127.0.0.1", port)).unwrap();
    assert!(kill_port(port));
    let status = server.0.wait().unwrap();
    assert_eq!(status.signal(), Some(9), "{status}");
    drop(client);
    assert!(!kill_port(port), "nothing listens any more");
}
