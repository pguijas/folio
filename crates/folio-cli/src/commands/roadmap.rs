//! `folio roadmap`: the phase table of the `roadmap:` section; folio-plugins
//! normalizes, this file renders.

use folio_plugins::roadmap::table_rows;
use folio_plugins::{get_phases, PluginHost};

use crate::cli::RoadmapArgs;
use crate::error::CliError;
use crate::pipeline::{load_config, plugin_host};
use crate::ui::table::{Cell, Column, Justify, Table};
use crate::ui::text::{BOLD, CYAN, PLAIN, YELLOW};
use crate::ui::Ui;
use crate::PluginFactory;

/// Print the configured phases; no phases is a yellow note and exit 0.
pub fn run(ui: &Ui, args: RoadmapArgs, plugins: &[PluginFactory]) -> Result<(), CliError> {
    let target = args.project.resolve()?;
    let loaded = load_config(&target.join(&args.config), &target, &plugin_host(plugins))
        .map_err(CliError::message)?;
    let mut warnings = loaded.warnings;
    let mut config = loaded.config;
    PluginHost::builtin()
        .configure(&mut config, &loaded.raw, &mut warnings)
        .map_err(CliError::message)?;
    for warning in &warnings {
        ui.eprint_styled(YELLOW, &format!("warning: {warning}"));
    }
    let phases = get_phases(&config);
    if phases.is_empty() {
        ui.print_styled(YELLOW, "No roadmap phases configured in docs.yaml.");
        return Ok(());
    }
    let mut table = Table::new(
        &format!("{} Roadmap", config.project.name),
        vec![
            Column::new("Project", Justify::Left, PLAIN),
            Column::new("Status", Justify::Left, CYAN),
            Column::new("Version", Justify::Left, PLAIN),
            Column::new("Title", Justify::Left, BOLD),
            Column::new("Command", Justify::Left, PLAIN),
        ],
    );
    for row in table_rows(&phases) {
        table.add_row(row.into_iter().map(Cell::new).collect());
    }
    ui.blank();
    ui.print_lines(&table.render(ui.colors));
    ui.blank();
    Ok(())
}
