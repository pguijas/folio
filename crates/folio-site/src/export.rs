//! Export and serve orchestration over a prepared `SiteBuilder`: the static
//! export with its streamed log, the LLM files placed after it, and the dev
//! server start.

use std::process::Child;

use crate::builder::SiteBuilder;
use crate::Result;

/// What a static export produced, for the binary's step rows and panel.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct ExportResult {
    /// The LLM files written, in `llms.txt`, `llms-full.txt` order.
    pub llm_files: Vec<&'static str>,
    /// Every line `pnpm run build` printed, as received.
    pub output_lines: Vec<String>,
    /// Rewriter warnings (a drifted Turbopack runtime shape).
    pub warnings: Vec<String>,
}

impl ExportResult {
    /// The `Export` step detail: `Site export completed` plus the LLM files.
    pub fn detail(&self) -> String {
        let mut detail = "Site export completed".to_string();
        for name in &self.llm_files {
            detail.push_str(", ");
            detail.push_str(name);
        }
        detail
    }
}

/// The body of the `Build output` panel: the joined lines without trailing
/// whitespace, or a placeholder when nothing was printed.
pub fn build_output_text(lines: &[String]) -> String {
    let text = lines.concat();
    let trimmed = text.trim_end();
    if trimmed.is_empty() {
        "Waiting for build output...".to_string()
    } else {
        trimmed.to_string()
    }
}

fn llm_names(llms_txt: Option<&str>, llms_full_txt: Option<&str>) -> Vec<&'static str> {
    [("llms.txt", llms_txt), ("llms-full.txt", llms_full_txt)]
        .into_iter()
        .filter(|(_, text)| text.is_some())
        .map(|(name, _)| name)
        .collect()
}

impl SiteBuilder<'_> {
    /// `folio build`: run the frontend export (log in `.build/.folio-build.log`),
    /// then place the LLM files in the output dir. A failed export returns
    /// `SiteError::Build` carrying the streamed lines.
    pub fn export_static_site(
        &self,
        llms_txt: Option<&str>,
        llms_full_txt: Option<&str>,
    ) -> Result<ExportResult> {
        let mut lines = Vec::new();
        let warnings = self.build(None, &mut |line| lines.push(line.to_string()))?;
        self.write_llm_files(llms_txt, llms_full_txt, false)?;
        Ok(ExportResult {
            llm_files: llm_names(llms_txt, llms_full_txt),
            output_lines: lines,
            warnings,
        })
    }

    /// `folio serve`: place the LLM files under `public/` and start `next dev`.
    pub fn serve_site(
        &self,
        llms_txt: Option<&str>,
        llms_full_txt: Option<&str>,
        port: u16,
        kill_existing: bool,
        on_line: Box<dyn FnMut(&str) + Send>,
    ) -> Result<(Vec<&'static str>, Option<Child>)> {
        self.write_llm_files(llms_txt, llms_full_txt, true)?;
        let child = self.serve(port, kill_existing, on_line)?;
        Ok((llm_names(llms_txt, llms_full_txt), child))
    }
}

#[cfg(test)]
#[path = "export_tests.rs"]
mod tests;
