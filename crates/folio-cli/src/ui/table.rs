//! Heavy-head box tables (rich `Table`, box `HEAVY_HEAD`) for `folio
//! coverage` and `folio roadmap`.

use anstyle::Style;

use super::text::{cell_len, center_margin, merge, paint, Colors, BOLD, ITALIC, PLAIN};

/// Cell alignment within a column.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Justify {
    Left,
    Right,
}

/// A column: header, alignment and the style its cells inherit.
pub struct Column {
    pub header: String,
    pub justify: Justify,
    pub style: Style,
}

impl Column {
    /// A column.
    pub fn new(header: &str, justify: Justify, style: Style) -> Column {
        Column {
            header: header.to_string(),
            justify,
            style,
        }
    }
}

/// One cell: text plus a style layered over the column's.
pub struct Cell {
    pub text: String,
    pub style: Style,
}

impl Cell {
    /// A cell in the column's style.
    pub fn new(text: impl Into<String>) -> Cell {
        Cell {
            text: text.into(),
            style: PLAIN,
        }
    }

    /// A cell with its own style.
    pub fn styled(text: impl Into<String>, style: Style) -> Cell {
        Cell {
            text: text.into(),
            style,
        }
    }
}

/// A titled table with optional section rules.
pub struct Table {
    pub title: Option<String>,
    pub columns: Vec<Column>,
    pub rows: Vec<Vec<Cell>>,
    /// Row indexes preceded by a section rule (rich `add_section`).
    pub sections_before: Vec<usize>,
}

impl Table {
    /// An empty table.
    pub fn new(title: &str, columns: Vec<Column>) -> Table {
        Table {
            title: Some(title.to_string()),
            columns,
            rows: Vec::new(),
            sections_before: Vec::new(),
        }
    }

    /// Append a row.
    pub fn add_row(&mut self, cells: Vec<Cell>) {
        self.rows.push(cells);
    }

    /// Start a new section before the next row.
    pub fn add_section(&mut self) {
        self.sections_before.push(self.rows.len());
    }

    fn widths(&self) -> Vec<usize> {
        self.columns
            .iter()
            .enumerate()
            .map(|(i, column)| {
                self.rows
                    .iter()
                    .filter_map(|row| row.get(i))
                    .map(|cell| cell_len(&cell.text))
                    .chain(std::iter::once(cell_len(&column.header)))
                    .max()
                    .unwrap_or(0)
            })
            .collect()
    }

    fn rule(widths: &[usize], left: &str, fill: &str, cross: &str, right: &str) -> String {
        let segments: Vec<String> = widths.iter().map(|w| fill.repeat(w + 2)).collect();
        format!("{left}{}{right}", segments.join(cross))
    }

    fn row(
        &self,
        widths: &[usize],
        cells: &[(String, Style)],
        bar: &str,
        colors: Colors,
    ) -> String {
        let mut out = String::from(bar);
        for (i, width) in widths.iter().enumerate() {
            let (text, style) = cells.get(i).cloned().unwrap_or_default();
            let pad = " ".repeat(width.saturating_sub(cell_len(&text)));
            let painted = paint(style, &text, colors);
            let aligned = match self.columns[i].justify {
                Justify::Left => format!("{painted}{pad}"),
                Justify::Right => format!("{pad}{painted}"),
            };
            out.push_str(&format!(" {aligned} {bar}"));
        }
        out
    }

    /// The table, one string per row; the title centred above it.
    pub fn render(&self, colors: Colors) -> Vec<String> {
        let widths = self.widths();
        let table_width = widths.iter().map(|w| w + 3).sum::<usize>() + 1;
        let mut lines = Vec::new();
        if let Some(title) = &self.title {
            let margin = " ".repeat(center_margin(cell_len(title), table_width));
            lines.push(format!("{margin}{}", paint(ITALIC, title, colors)));
        }
        lines.push(Self::rule(&widths, "┏", "━", "┳", "┓"));
        let headers: Vec<(String, Style)> = self
            .columns
            .iter()
            .map(|c| (c.header.clone(), BOLD))
            .collect();
        lines.push(self.row(&widths, &headers, "┃", colors));
        lines.push(Self::rule(&widths, "┡", "━", "╇", "┩"));
        for (index, row) in self.rows.iter().enumerate() {
            if self.sections_before.contains(&index) {
                lines.push(Self::rule(&widths, "├", "─", "┼", "┤"));
            }
            let cells: Vec<(String, Style)> = row
                .iter()
                .enumerate()
                .map(|(i, cell)| (cell.text.clone(), merge(self.columns[i].style, cell.style)))
                .collect();
            lines.push(self.row(&widths, &cells, "│", colors));
        }
        lines.push(Self::rule(&widths, "└", "─", "┴", "┘"));
        lines
    }
}

#[cfg(test)]
#[path = "table_tests.rs"]
mod tests;
