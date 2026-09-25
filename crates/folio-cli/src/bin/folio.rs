//! The `folio` binary: the Docs CLI host with no extensions mounted.

fn main() -> std::process::ExitCode {
    folio_cli::run(&[], &[])
}
