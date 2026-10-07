//! The `folioh` binary: the Docs CLI host with no extensions mounted.

fn main() -> std::process::ExitCode {
    folioh_cli::run(&[], &[])
}
