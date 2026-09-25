use super::*;

#[test]
fn export_detail_and_panel_text() {
    let result = ExportResult {
        llm_files: vec!["llms.txt", "llms-full.txt"],
        output_lines: vec!["a\n".into(), "b  \n".into()],
        warnings: vec![],
    };
    assert_eq!(
        result.detail(),
        "Site export completed, llms.txt, llms-full.txt"
    );
    assert_eq!(ExportResult::default().detail(), "Site export completed");
    assert_eq!(build_output_text(&result.output_lines), "a\nb");
    assert_eq!(build_output_text(&[]), "Waiting for build output...");
}
