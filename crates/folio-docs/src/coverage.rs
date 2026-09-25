//! Docstring coverage as data: per-module counts, the aggregate, the `--min`
//! verdict and the colour thresholds. The binary renders the table.

use folio_ir::{ClassIR, FunctionIR, ModuleIR};
use indexmap::IndexMap;

/// The `folio coverage` failure when the Python roots yield nothing.
pub const NO_MODULES_ERROR: &str = "No Python modules found. Check source paths in docs.yaml.";

/// Counts for one module or the whole project; `undocumented` lists fqns.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct CoverageResult {
    pub total: usize,
    pub documented: usize,
    pub undocumented: Vec<String>,
}

impl CoverageResult {
    /// `documented / total * 100`; an empty set is fully covered.
    pub fn percentage(&self) -> f64 {
        if self.total == 0 {
            100.0
        } else {
            self.documented as f64 / self.total as f64 * 100.0
        }
    }
}

/// The colour band of a percentage in the coverage table.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CoverageLevel {
    /// 80% and above (green).
    High,
    /// 50% to 80% (yellow).
    Medium,
    /// Below 50% (red).
    Low,
}

/// The band a percentage falls in.
pub fn coverage_level(percentage: f64) -> CoverageLevel {
    if percentage >= 80.0 {
        CoverageLevel::High
    } else if percentage >= 50.0 {
        CoverageLevel::Medium
    } else {
        CoverageLevel::Low
    }
}

/// The `--min` verdict: the failure line when `min > 0` and the total is below it.
pub fn below_minimum(total_percentage: f64, min: f64) -> Option<String> {
    (min > 0.0 && total_percentage < min)
        .then(|| format!("Coverage {total_percentage:.1}% is below minimum {min:.1}%"))
}

/// Private = leading `_`, except `__init__`.
fn is_private(name: &str) -> bool {
    name.starts_with('_') && name != "__init__"
}

fn documented(short_description: &str) -> bool {
    !short_description.trim().is_empty()
}

struct Tally {
    documented: usize,
    undocumented: Vec<String>,
}

impl Tally {
    fn record(&mut self, fqn: String, is_documented: bool) {
        if is_documented {
            self.documented += 1;
        } else {
            self.undocumented.push(fqn);
        }
    }

    fn function(&mut self, func: &FunctionIR, prefix: &str) {
        if !is_private(&func.name) {
            self.record(
                format!("{prefix}.{}", func.name),
                documented(&func.docstring.short_description),
            );
        }
    }

    fn class(&mut self, class: &ClassIR, prefix: &str) {
        if is_private(&class.name) {
            return;
        }
        let fqn = format!("{prefix}.{}", class.name);
        self.record(fqn.clone(), documented(&class.docstring.short_description));
        for method in &class.methods {
            self.function(method, &fqn);
        }
        for inner in &class.inner_classes {
            self.class(inner, &fqn);
        }
    }
}

/// The module itself, its public functions and public classes with their
/// public methods and inner classes. Constants and types do not count.
pub fn analyze_module(module: &ModuleIR) -> CoverageResult {
    let mut tally = Tally {
        documented: 0,
        undocumented: Vec::new(),
    };
    tally.record(
        module.name.clone(),
        documented(&module.docstring.short_description),
    );
    for func in &module.functions {
        tally.function(func, &module.name);
    }
    for class in &module.classes {
        tally.class(class, &module.name);
    }
    CoverageResult {
        total: tally.documented + tally.undocumented.len(),
        documented: tally.documented,
        undocumented: tally.undocumented,
    }
}

/// One result per module, in module order.
pub fn analyze_modules(modules: &[ModuleIR]) -> IndexMap<String, CoverageResult> {
    modules
        .iter()
        .map(|module| (module.name.clone(), analyze_module(module)))
        .collect()
}

/// The project total: sums, and the undocumented lists concatenated in order.
pub fn aggregate(results: &IndexMap<String, CoverageResult>) -> CoverageResult {
    results
        .values()
        .fold(CoverageResult::default(), |mut total, result| {
            total.total += result.total;
            total.documented += result.documented;
            total
                .undocumented
                .extend(result.undocumented.iter().cloned());
            total
        })
}

#[cfg(test)]
#[path = "coverage_tests.rs"]
mod tests;
