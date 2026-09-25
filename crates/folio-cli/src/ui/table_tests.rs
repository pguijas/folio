use super::*;
use crate::ui::text::{CYAN, GREEN, YELLOW};

fn coverage_table() -> Table {
    let mut table = Table::new(
        "Documentation Coverage",
        vec![
            Column::new("Module", Justify::Left, CYAN),
            Column::new("Total", Justify::Right, PLAIN),
            Column::new("Documented", Justify::Right, PLAIN),
            Column::new("Coverage", Justify::Right, PLAIN),
        ],
    );
    table.add_row(vec![
        Cell::new("demo"),
        Cell::new("4"),
        Cell::new("4"),
        Cell::styled("100.0%", GREEN),
    ]);
    table.add_row(vec![
        Cell::new("demo.core"),
        Cell::new("6"),
        Cell::new("3"),
        Cell::styled("50.0%", YELLOW),
    ]);
    table.add_section();
    table.add_row(vec![
        Cell::styled("Total", BOLD),
        Cell::styled("10", BOLD),
        Cell::styled("7", BOLD),
        Cell::styled(
            "70.0%",
            BOLD.fg_color(Some(anstyle::AnsiColor::Yellow.into())),
        ),
    ]);
    table
}

#[test]
fn renders_the_heavy_head_box_with_right_justified_numbers() {
    let lines = coverage_table().render(Colors::Off);
    assert_eq!(
        lines,
        vec![
            "           Documentation Coverage",
            "┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓",
            "┃ Module    ┃ Total ┃ Documented ┃ Coverage ┃",
            "┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩",
            "│ demo      │     4 │          4 │   100.0% │",
            "│ demo.core │     6 │          3 │    50.0% │",
            "├───────────┼───────┼────────────┼──────────┤",
            "│ Total     │    10 │          7 │    70.0% │",
            "└───────────┴───────┴────────────┴──────────┘",
        ]
    );
}

#[test]
fn colours_layer_the_cell_style_over_the_column_style() {
    let lines = coverage_table().render(Colors::TrueColor);
    assert!(lines[0].contains("\x1b[3mDocumentation Coverage\x1b[0m"));
    assert!(lines[2].contains("\x1b[1mModule\x1b[0m"));
    assert!(lines[4].contains("\x1b[36mdemo\x1b[0m"));
    assert!(lines[4].contains("\x1b[32m100.0%\x1b[0m"));
    assert!(lines[7].contains("\x1b[1m\x1b[36mTotal\x1b[0m"));
    assert!(lines[7].contains("\x1b[1m\x1b[33m70.0%\x1b[0m"));
}
