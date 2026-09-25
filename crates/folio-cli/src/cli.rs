//! The clap command tree: every command, option and argument of the `folio`
//! binary, with their help texts.
//! Commands are listed in the CLI guide's order; `build-versions` and the
//! `github-pages` group are hidden.

use std::path::PathBuf;

use clap::{Args, Parser, Subcommand};

use crate::commands::github_pages;

#[derive(Parser, Debug)]
#[command(
    name = "folio",
    version,
    about = "Build documentation from source and guides.",
    arg_required_else_help = true,
    disable_help_subcommand = true,
    disable_version_flag = true
)]
/// The `folio` command line: the eager `--version` flag, the `--update`
/// flag that runs on its own, and one subcommand.
pub struct Cli {
    /// Eager: prints `folio <version>` and exits before any subcommand runs.
    #[arg(short = 'V', long, action = clap::ArgAction::Version, help = "Show version")]
    pub version: (),
    /// Replaces this binary with the latest GitHub release; `run` refuses it
    /// next to a subcommand.
    #[arg(long, help = "Update folio to the latest release and exit")]
    pub update: bool,
    /// Absent only with `--update`: a bare `folio` shows its help instead.
    #[command(subcommand)]
    pub command: Option<Command>,
}

/// Every subcommand in the CLI guide's order; the hidden ones last.
#[derive(Subcommand, Debug)]
pub enum Command {
    #[command(about = "Initialize a new Folio documentation project.")]
    Init(InitArgs),
    #[command(about = "Build the documentation site into the output directory.")]
    Build(BuildArgs),
    #[command(about = "Build and serve the site locally, rebuilding as sources change.")]
    Serve(ServeArgs),
    #[command(about = "Analyze documentation coverage of Python source files.")]
    Coverage(CoverageArgs),
    #[command(about = "Remove the build cache and the generated output directory.")]
    Clean(CleanArgs),
    #[command(about = "Preview source-defined roadmap phases.")]
    Roadmap(RoadmapArgs),
    #[command(
        name = "build-versions",
        hide = true,
        about = "Build docs for all configured versions."
    )]
    BuildVersions(BuildVersionsArgs),
    #[command(name = "github-pages", hide = true, subcommand)]
    GithubPages(github_pages::Cmd),
}

// `[DIRECTORY]` plus `--project-dir`, shared by build, build-versions, serve,
// coverage, clean and roadmap. A plain comment: clap would lift a doc comment
// into the `about` of every command that has none.
#[derive(Args, Debug, Default)]
pub struct ProjectArgs {
    #[arg(value_name = "DIRECTORY", help = "Project directory (defaults to cwd)")]
    pub directory: Option<PathBuf>,
    #[arg(
        long = "project-dir",
        value_name = "PATH",
        help = "Compatibility option for scripts that prefer named arguments"
    )]
    pub project_dir: Option<PathBuf>,
}

// The argument structs carry no doc comments: clap lifts a flattened or
// tuple struct's doc into the `about` of a command that has none (build,
// serve, clean); their options document themselves through `help`.
#[derive(Args, Debug)]
pub struct InitArgs {
    #[arg(value_name = "DIRECTORY", help = "Project directory (defaults to cwd)")]
    pub directory: Option<PathBuf>,
    #[arg(short = 'y', long, help = "Skip prompts, use detected defaults")]
    pub yes: bool,
}

#[derive(Args, Debug)]
pub struct BuildArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(short = 'v', long, help = "Show detailed output")]
    pub verbose: bool,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
    #[arg(long, help = "Force full rebuild (clear cache)")]
    pub clean: bool,
    #[arg(
        short = 'o',
        long,
        help = "Starts a static preview in the browser and blocks until interrupted"
    )]
    pub open: bool,
    #[arg(
        short = 'p',
        long,
        default_value_t = 8787,
        requires = "open",
        help = "Port for the --open static preview"
    )]
    pub port: u16,
}

#[derive(Args, Debug)]
pub struct BuildVersionsArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(short = 'v', long, help = "Show detailed output")]
    pub verbose: bool,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
    #[arg(long, help = "Force full rebuild (clear cache)")]
    pub clean: bool,
}

#[derive(Args, Debug)]
pub struct ServeArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(short = 'v', long, help = "Show detailed output")]
    pub verbose: bool,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
    #[arg(
        short = 'p',
        long,
        value_name = "INT",
        default_value_t = 4321,
        help = "Dev server port"
    )]
    pub port: u16,
    #[arg(short = 'o', long, help = "Open browser automatically")]
    pub open: bool,
    #[arg(long, help = "Force full rebuild (clear cache)")]
    pub clean: bool,
    #[arg(
        long,
        help = "Build the example projects under docs/examples before serving, a full nested site each"
    )]
    pub previews: bool,
    #[arg(
        long,
        hide = true,
        help = "Build and serve every configured version as a static preview"
    )]
    pub versions: bool,
    #[arg(
        long = "kill-existing",
        help = "Stop an existing process on the selected port before serving"
    )]
    pub kill_existing: bool,
}

#[derive(Args, Debug)]
pub struct CoverageArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
    #[arg(short = 'v', long, help = "List each undocumented symbol")]
    pub verbose: bool,
    #[arg(
        long,
        value_name = "FLOAT",
        default_value_t = 0.0,
        help = "Minimum coverage percentage (exit 1 if below)"
    )]
    pub min: f64,
}

#[derive(Args, Debug)]
pub struct CleanArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
}

#[derive(Args, Debug)]
pub struct RoadmapArgs {
    #[command(flatten)]
    pub project: ProjectArgs,
    #[arg(
        short = 'c',
        long,
        value_name = "TEXT",
        default_value = "docs.yaml",
        help = "Config file path"
    )]
    pub config: String,
}

#[cfg(test)]
#[path = "cli_tests.rs"]
mod tests;
