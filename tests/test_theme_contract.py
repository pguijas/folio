# tests/test_theme_contract.py
from folio.schemas import theme_contract as tc


def test_tune_keys_match_config():
    # the contract is the source; config must import it (Task 2 wires this)
    assert tc.THEME_TUNE_KEYS == {
        "fontId",
        "colorId",
        "surfaceColorId",
        "shellPaddingId",
        "contentWidthId",
        "rhythmId",
        "borderId",
        "codeTreatmentId",
    }


def test_aliases_cover_user_facing_names():
    assert tc.THEME_TUNE_ALIASES["accent"] == "colorId"
    assert tc.THEME_TUNE_ALIASES["font"] == "fontId"
    assert tc.THEME_TUNE_ALIASES["width"] == "contentWidthId"
    # every alias target is a canonical key
    assert set(tc.THEME_TUNE_ALIASES.values()) <= tc.THEME_TUNE_KEYS


def test_style_properties_are_css_custom_props():
    assert all(p.startswith("--folio-") for p in tc.THEME_STYLE_PROPERTIES)
    assert "--folio-card-shadow" in tc.THEME_STYLE_PROPERTIES
    assert "--folio-workspace-shell-topbar-border" in tc.THEME_STYLE_PROPERTIES


def test_radius_options_are_the_fixed_scale():
    assert tc.THEME_RADIUS_OPTIONS == ["0", "0.3rem", "0.5rem", "0.75rem", "1rem"]


def test_token_names_list_removed():
    # THEME_TOKEN_NAMES had zero consumers and was removed; keep it removed.
    assert not hasattr(tc, "THEME_TOKEN_NAMES")


def test_codegen_emits_all_style_props():
    from folio.generator.theme_contract_codegen import generate_typescript_contract

    out = generate_typescript_contract()
    assert "// GENERATED FILE - DO NOT EDIT" in out
    assert '"--folio-card-shadow"?: string' in out
    assert "export type ThemeTuneKey =" in out


def test_codegen_emits_radius_scale():
    from folio.generator.theme_contract_codegen import generate_typescript_contract

    out = generate_typescript_contract()
    assert (
        'export const themeRadiusScale = ["0", "0.3rem", "0.5rem", "0.75rem", "1rem"] as const'
        in out
    )


def test_codegen_matches_committed_file():
    from folio.generator.theme_contract_codegen import generate_typescript_contract
    from pathlib import Path

    generated = generate_typescript_contract()
    committed_path = (
        Path(__file__).parent.parent
        / "template"
        / "theme"
        / "theme-contract.generated.ts"
    )
    if committed_path.exists():
        committed = committed_path.read_text(encoding="utf-8")
        assert generated == committed, (
            "Generated TypeScript contract does not match committed file. Run: python -c 'from folio.generator.theme_contract_codegen import generate_typescript_contract; from pathlib import Path; Path(\"template/theme/theme-contract.generated.ts\").write_text(generate_typescript_contract())'"
        )
