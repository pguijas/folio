//! `folio coverage`: the per-module docstring coverage table and the `--min`
//! verdict; folio-docs counts, this file renders.

use folio_docs::{
    aggregate, analyze_modules, below_minimum, coverage_level, parse_python_sources, CoverageLevel,
    NO_MODULES_ERROR,
};

use crate::cli::CoverageArgs;
use crate::error::CliError;
use crate::pipeline::{load_config, plugin_host};
use crate::ui::table::{Cell, Column, Justify, Table};
use crate::ui::text::{BOLD, CYAN, GREEN, PLAIN, RED, YELLOW};
use crate::ui::Ui;
use crate::PluginFactory;

fn level_style(percentage: f64) -> anstyle::Style {
    match coverage_level(percentage) {
        CoverageLevel::High => GREEN,
        CoverageLevel::Medium => YELLOW,
        CoverageLevel::Low => RED,
    }
}

/// Analyze the Python roots and print the table; exit 1 below `--min`.
pub fn run(ui: &Ui, args: CoverageArgs, plugins: &[PluginFactory]) -> Result<(), CliError> {
    let target = args.project.resolve()?;
    let loaded = load_config(&target.join(&args.config), &target, &plugin_host(plugins))
        .map_err(CliError::message)?;
    for warning in &loaded.warnings {
        ui.eprint_styled(YELLOW, &format!("warning: {warning}"));
    }
    // JavaScript and Rust sources build, but their coverage is not counted
    // yet: a config without Python paths is refused rather than reported
    // as a project with nothing in it.
    if loaded.config.language_source("python").paths.is_empty() {
        return Err(CliError::Message(format!(
            "folio coverage reads Python sources only in this release, and {} lists no source.python paths.",
            args.config
        )));
    }
    let resolved = loaded
        .config
        .resolve_paths(&target)
        .map_err(CliError::message)?;
    let parsed = parse_python_sources(&resolved).map_err(CliError::message)?;
    for missing in &parsed.missing_paths {
        ui.eprint_styled(
            YELLOW,
            &format!("Warning: Python source path not found: {missing}"),
        );
    }
    if parsed.modules.is_empty() {
        return Err(CliError::Message(NO_MODULES_ERROR.to_string()));
    }
    let results = analyze_modules(&parsed.modules);
    let total = aggregate(&results);

    let mut table = Table::new(
        "Documentation Coverage",
        vec![
            Column::new("Module", Justify::Left, CYAN),
            Column::new("Total", Justify::Right, PLAIN),
            Column::new("Documented", Justify::Right, PLAIN),
            Column::new("Coverage", Justify::Right, PLAIN),
        ],
    );
    for (name, result) in &results {
        let pct = result.percentage();
        table.add_row(vec![
            Cell::new(name.as_str()),
            Cell::new(result.total.to_string()),
            Cell::new(result.documented.to_string()),
            Cell::styled(format!("{pct:.1}%"), level_style(pct)),
        ]);
    }
    table.add_section();
    let total_pct = total.percentage();
    table.add_row(vec![
        Cell::styled("Total", BOLD),
        Cell::styled(total.total.to_string(), BOLD),
        Cell::styled(total.documented.to_string(), BOLD),
        Cell::styled(format!("{total_pct:.1}%"), level_style(total_pct).bold()),
    ]);
    ui.blank();
    ui.print_lines(&table.render(ui.colors));
    if args.verbose && !total.undocumented.is_empty() {
        ui.blank();
        ui.print_styled(BOLD, "Undocumented:");
        let mut names = total.undocumented.clone();
        names.sort();
        for name in names {
            ui.print(&format!("  {name}"));
        }
    }
    ui.blank();
    if let Some(verdict) = below_minimum(total_pct, args.min) {
        ui.eprint_styled(RED, &verdict);
        return Err(CliError::Exit(1));
    }
    Ok(())
}
