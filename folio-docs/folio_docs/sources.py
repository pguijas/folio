from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from folio_docs.config import Config
from folio_docs.ir import ModuleIR
from folio_docs.parser.markdown_parser import MarkdownResult, parse_markdown_directory
from folio_docs.parser.python_parser import (
    _is_python_import_root,
    parse_python_directory,
    parse_python_source_root,
)


@dataclass
class ParsedPythonSources:
    modules: list[ModuleIR] = field(default_factory=list)
    scanned_paths: list[Path] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)


@dataclass
class ParsedDocSources:
    docs: list[MarkdownResult] = field(default_factory=list)
    scanned_paths: list[Path] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)


def parse_python_sources(config: Config) -> ParsedPythonSources:
    result = ParsedPythonSources()
    for src in config.python_sources:
        src_path = Path(src)
        if not src_path.exists():
            result.missing_paths.append(src)
            continue
        result.scanned_paths.append(src_path)
        if _is_python_import_root(src_path):
            modules = parse_python_source_root(
                str(src_path),
                excludes=config.python_excludes,
                docstring_style=config.docstring_style,
            )
        else:
            modules = parse_python_directory(
                str(src_path),
                src_path.name,
                excludes=config.python_excludes,
                docstring_style=config.docstring_style,
            )
        result.modules.extend(modules)
    return result


def parse_doc_sources(config: Config) -> ParsedDocSources:
    result = ParsedDocSources()
    for doc_dir in config.doc_sources:
        doc_path = Path(doc_dir)
        if not doc_path.exists():
            result.missing_paths.append(doc_dir)
            continue
        result.scanned_paths.append(doc_path)
        docs = parse_markdown_directory(str(doc_path), route_prefix="")
        result.docs.extend(docs)
    return result
