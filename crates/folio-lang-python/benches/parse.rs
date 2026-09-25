//! Parse-throughput benchmark for `folio-lang-python`.
//!
//! Run with:  cargo bench -p folio-lang-python
//! Corpus:    all `*.py` under $FOLIO_BENCH_CORPUS (defaults to the checked-in
//!            Python fixtures). Every file is read once, up front, so the measured
//!            region is pure parsing plus docstring finalization: no disk I/O.
use std::path::PathBuf;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use folio_lang_python::{discover, finalize_module, parse_source_raw, DocstringStyle};

/// (path, source, module_name) for every `*.py` discovery finds under the corpus dir.
fn load_corpus() -> Vec<(String, String, String)> {
    let root = std::env::var("FOLIO_BENCH_CORPUS")
        .unwrap_or_else(|_| format!("{}/tests/fixtures", env!("CARGO_MANIFEST_DIR")));
    let roots = [PathBuf::from(root)];
    discover(&roots, &[])
        .into_iter()
        .map(|f| {
            let src = std::fs::read_to_string(&f.path).expect("read fixture");
            (f.path.to_string_lossy().into_owned(), src, f.module_name)
        })
        .collect()
}

fn parse(src: &str, module: &str, path: &str) -> folio_ir::ModuleIR {
    let raw = parse_source_raw(src, module, path).expect("parse");
    finalize_module(raw, DocstringStyle::Auto)
}

fn bench_parse(c: &mut Criterion) {
    let corpus = load_corpus();
    assert!(!corpus.is_empty(), "empty bench corpus");
    let total_bytes: u64 = corpus.iter().map(|(_, s, _)| s.len() as u64).sum();

    // 1) Whole-corpus throughput (bytes/sec): the headline number.
    let mut group = c.benchmark_group("parse_corpus");
    group.throughput(Throughput::Bytes(total_bytes));
    group.bench_function("all_fixtures", |b| {
        b.iter(|| {
            for (path, src, module) in &corpus {
                criterion::black_box(parse(src, module, path));
            }
        })
    });
    group.finish();

    // 2) Per-file timings for the largest fixtures: catches per-shape regressions.
    let mut big = corpus.clone();
    big.sort_by_key(|(_, s, _)| std::cmp::Reverse(s.len()));
    let mut per = c.benchmark_group("parse_file");
    for (path, src, module) in big.into_iter().take(8) {
        per.throughput(Throughput::Bytes(src.len() as u64));
        let id = BenchmarkId::from_parameter(
            std::path::Path::new(&path)
                .file_name()
                .unwrap()
                .to_string_lossy(),
        );
        per.bench_with_input(id, &(path, src, module), |b, (path, src, module)| {
            b.iter(|| criterion::black_box(parse(src, module, path)))
        });
    }
    per.finish();
}

criterion_group!(benches, bench_parse);
criterion_main!(benches);
