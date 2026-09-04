# tests/test_theme_package_validator.py
import pytest
from folio.generator.theme_package_validator import (
    _validate_theme_package,
    validate_and_raise,
)


def test_missing_path_errors(tmp_path):
    errs = _validate_theme_package(tmp_path / "nope")
    assert errs and "not found" in errs[0]


def test_reserved_content_dir_errors(tmp_path):
    (tmp_path / "content").mkdir()
    errs = _validate_theme_package(tmp_path)
    assert any("content/" in e for e in errs)


def test_reserved_generated_theme_contract_file_errors(tmp_path):
    # theme/theme-contract.generated.ts is Folio-owned codegen output: a
    # package copy would be clobbered on every build, so shipping it is an
    # error rather than a silent overwrite.
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "theme-contract.generated.ts").write_text("export const stale = 1\n")
    errs = _validate_theme_package(tmp_path)
    assert any("theme/theme-contract.generated.ts" in e for e in errs)


def test_package_owned_project_theme_alone_is_not_reserved(tmp_path):
    # Packages may own theme/project-theme.ts (documented ownership model);
    # only the generated contract file is reserved.
    _write_project_theme(
        tmp_path,
        "export const projectThemePreset = 1\n"
        "export const projectThemeDefaultConfig = {}\n",
    )
    assert _validate_theme_package(tmp_path) == []


def test_project_theme_missing_export_errors(tmp_path):
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "project-theme.ts").write_text("export const nope = 1\n")
    errs = _validate_theme_package(tmp_path)
    assert any("projectThemePreset" in e for e in errs)


def _write_project_theme(tmp_path, content):
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "project-theme.ts").write_text(content)


def test_project_theme_const_export_ok(tmp_path):
    _write_project_theme(
        tmp_path,
        "export const projectThemePreset = 1\n"
        "export const projectThemeDefaultConfig = {}\n",
    )
    errs = _validate_theme_package(tmp_path)
    assert not any("must export" in e for e in errs)


def test_project_theme_aliased_reexport_ok(tmp_path):
    _write_project_theme(
        tmp_path,
        "export { foo as projectThemePreset }\n"
        "export { bar as projectThemeDefaultConfig }\n",
    )
    errs = _validate_theme_package(tmp_path)
    assert not any("must export" in e for e in errs)


def test_project_theme_suffixed_name_does_not_false_pass(tmp_path):
    # `projectThemePresetX` must NOT satisfy the `projectThemePreset` export.
    _write_project_theme(
        tmp_path,
        "export const projectThemePresetX = 1\n"
        "export const projectThemeDefaultConfig = {}\n",
    )
    errs = _validate_theme_package(tmp_path)
    assert any("must export 'projectThemePreset'" in e for e in errs)


def test_project_theme_source_side_alias_does_not_count(tmp_path):
    # `export { projectThemePreset as foo }` exports `foo`, not
    # `projectThemePreset`, so the required export is still missing.
    _write_project_theme(
        tmp_path,
        "export { projectThemePreset as foo }\n"
        "export const projectThemeDefaultConfig = {}\n",
    )
    errs = _validate_theme_package(tmp_path)
    assert any("must export 'projectThemePreset'" in e for e in errs)


def test_valid_minimal_package_ok(tmp_path):
    (tmp_path / "app").mkdir()
    assert _validate_theme_package(tmp_path) == []


def test_validate_and_raise(tmp_path):
    (tmp_path / "content").mkdir()
    with pytest.raises(ValueError, match="Theme package validation failed"):
        validate_and_raise(tmp_path)
