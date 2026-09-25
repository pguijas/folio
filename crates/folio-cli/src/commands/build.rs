//! `folio build`: the pipeline, then the optional static preview behind
//! `--open`.

use folio_config::resolve_output_dir;

use crate::cli::BuildArgs;
use crate::error::CliError;
use crate::pipeline::{
    load_config, plugin_host, preview, run_build, tracer_from_env, BuildOptions,
};
use crate::ui::text::YELLOW;
use crate::ui::Ui;
use crate::PluginFactory;

/// Build the site; with `--open` serve `output_dir` on port 8787 until interrupted.
pub fn run(ui: &Ui, args: BuildArgs, plugins: &[PluginFactory]) -> Result<(), CliError> {
    let target = args.project.resolve()?;
    let opts = BuildOptions {
        verbose: args.verbose,
        clean: args.clean,
        previews: true,
        plugins: plugins.to_vec(),
        ..BuildOptions::new(&args.config)
    };
    run_build(&target, &opts, ui, tracer_from_env(ui))?;
    if args.open {
        let config = load_config(&target.join(&args.config), &target, &plugin_host(plugins))
            .map_err(CliError::message)?
            .config;
        let site_dir = resolve_output_dir(&target, &config.output_dir, &config.source_roots())
            .map_err(CliError::message)?;
        ui.print_styled(
            YELLOW,
            "--open starts a static preview server and blocks until interrupted.",
        );
        preview::serve_static_site(ui, &site_dir, args.port, true, false)?;
    }
    Ok(())
}
