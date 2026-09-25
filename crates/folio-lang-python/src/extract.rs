//! ruff AST to `ModuleRaw`: module, class and function extraction with CPython's
//! bracket and depth limits.

use std::borrow::Cow;
use std::path::PathBuf;

use folio_ir::docstring::cleandoc;
use folio_ir::{ArgKind, FunctionKind};
use ruff_python_ast::token::{TokenKind, Tokens};
use ruff_python_ast::{Decorator, Expr, Stmt, StmtClassDef, StmtFunctionDef};
use ruff_python_parser::parse_module;
use ruff_text_size::{Ranged, TextSize};

use crate::error::{ErrorKind, PythonSyntaxError};
use crate::raw::{ArgRaw, ClassRaw, FunctionRaw, ModuleRaw, VarRaw};
use crate::unparse::{self, UnparseError};

/// CPython's tokenizer rejects the 201st simultaneously open bracket (`MAXLEVEL` in
/// `Parser/tokenizer.h`); ruff parses any depth, so the limit is mirrored here.
const MAX_PAREN_LEVEL: usize = 200;

/// Byte offset to 1-based line, and to a character-counted column.
struct LineIndex {
    newline_offsets: Vec<u32>,
}

impl LineIndex {
    fn new(source: &str) -> Self {
        Self {
            newline_offsets: source
                .char_indices()
                .filter(|&(_, ch)| ch == '\n')
                .map(|(i, _)| i as u32)
                .collect(),
        }
    }

    fn line_number(&self, offset: u32) -> u32 {
        match self.newline_offsets.binary_search(&offset) {
            Ok(pos) | Err(pos) => (pos + 1) as u32,
        }
    }

    /// 1-based `(line, column)`, the column in characters like `SyntaxError.offset`.
    fn line_col(&self, offset: u32, source: &str) -> (u32, u32) {
        let line = self.line_number(offset);
        let line_start = if line > 1 {
            self.newline_offsets
                .get((line - 2) as usize)
                .map(|o| o + 1)
                .unwrap_or(0)
        } else {
            0
        };
        let column = source
            .get(line_start as usize..offset as usize)
            .map(|prefix| prefix.chars().count() as u32)
            .unwrap_or(offset.saturating_sub(line_start))
            + 1;
        (line, column)
    }
}

/// `ast.get_docstring`: the first statement must be a plain string literal.
fn get_docstring(body: &[Stmt]) -> Option<String> {
    match body.first()? {
        Stmt::Expr(expr) => match expr.value.as_ref() {
            Expr::StringLiteral(s) => Some(cleandoc(s.value.to_str())),
            _ => None,
        },
        _ => None,
    }
}

/// Per-file context shared by the extraction functions.
struct Ctx<'a> {
    source: &'a str,
    source_file: &'a str,
    line_index: LineIndex,
}

impl Ctx<'_> {
    fn error(&self, message: &str, offset: TextSize, kind: ErrorKind) -> PythonSyntaxError {
        let (line, column) = self.line_index.line_col(offset.to_u32(), self.source);
        PythonSyntaxError {
            path: PathBuf::from(self.source_file),
            message: message.to_string(),
            line,
            column,
            kind,
        }
    }

    fn unparse(&self, expr: &Expr) -> Result<String, PythonSyntaxError> {
        unparse::try_unparse_expr(expr, self.source).map_err(|UnparseError::TooDeep| {
            self.error(
                "maximum recursion depth exceeded",
                expr.range().start(),
                ErrorKind::Recursion,
            )
        })
    }

    fn annotation(&self, expr: Option<&Expr>) -> Result<String, PythonSyntaxError> {
        expr.map_or(Ok(String::new()), |e| self.unparse(e))
    }

    fn unparse_all<'e>(
        &self,
        exprs: impl Iterator<Item = &'e Expr>,
    ) -> Result<Vec<String>, PythonSyntaxError> {
        exprs.map(|e| self.unparse(e)).collect()
    }

    /// Line of the `def`/`async`/`class` keyword: CPython's `lineno`, which excludes
    /// decorators and stays on the keyword line when the name continues on the next
    /// line. ruff's range starts at the first decorator, so scan past the last one.
    fn keyword_line(&self, node_start: TextSize, decorators: &[Decorator]) -> u32 {
        let mut pos = decorators
            .last()
            .map(|d| d.range().end())
            .unwrap_or(node_start)
            .to_usize();
        let bytes = self.source.as_bytes();
        while let Some(&b) = bytes.get(pos) {
            match b {
                b'#' => {
                    while bytes.get(pos).is_some_and(|&c| c != b'\n') {
                        pos += 1;
                    }
                }
                b' ' | b'\t' | b'\n' | b'\r' | b'\x0c' => pos += 1,
                _ => break,
            }
        }
        self.line_index.line_number(pos as u32)
    }
}

fn is_self_or_cls(name: &str) -> bool {
    name == "self" || name == "cls"
}

fn extract_function_raw(
    node: &StmtFunctionDef,
    ctx: &Ctx<'_>,
    is_in_class: bool,
) -> Result<FunctionRaw, PythonSyntaxError> {
    let params = &node.parameters;
    let mut args: Vec<ArgRaw> = Vec::new();

    let regular = params
        .posonlyargs
        .iter()
        .map(|p| (p, ArgKind::PositionalOnly))
        .chain(params.args.iter().map(|p| (p, ArgKind::Regular)));
    for (p, kind) in regular {
        let name = p.parameter.name.as_str();
        if is_self_or_cls(name) {
            continue;
        }
        args.push(ArgRaw {
            name: name.to_string(),
            annotation: ctx.annotation(p.parameter.annotation.as_deref())?,
            default: p.default.as_ref().map(|d| ctx.unparse(d)).transpose()?,
            kind,
        });
    }
    if let Some(vararg) = &params.vararg {
        if !is_self_or_cls(vararg.name.as_str()) {
            args.push(ArgRaw {
                name: vararg.name.to_string(),
                annotation: ctx.annotation(vararg.annotation.as_deref())?,
                default: None,
                kind: ArgKind::VarPositional,
            });
        }
    }
    for p in &params.kwonlyargs {
        let name = p.parameter.name.as_str();
        if is_self_or_cls(name) {
            continue;
        }
        args.push(ArgRaw {
            name: name.to_string(),
            annotation: ctx.annotation(p.parameter.annotation.as_deref())?,
            default: p.default.as_ref().map(|d| ctx.unparse(d)).transpose()?,
            kind: ArgKind::KeywordOnly,
        });
    }
    if let Some(kwarg) = &params.kwarg {
        if !is_self_or_cls(kwarg.name.as_str()) {
            args.push(ArgRaw {
                name: kwarg.name.to_string(),
                annotation: ctx.annotation(kwarg.annotation.as_deref())?,
                default: None,
                kind: ArgKind::VarKeyword,
            });
        }
    }

    let decorators = ctx.unparse_all(node.decorator_list.iter().map(|d| &d.expression))?;
    let kind = function_kind(&decorators, is_in_class);

    Ok(FunctionRaw {
        name: node.name.to_string(),
        args,
        returns_annotation: ctx.annotation(node.returns.as_deref())?,
        decorators,
        docstring_raw: get_docstring(&node.body),
        is_async: node.is_async,
        source_file: ctx.source_file.to_string(),
        line_number: ctx.keyword_line(node.range().start(), &node.decorator_list),
        kind,
    })
}

/// The text before the first `(`, then after the last `.`: `functools.lru_cache(maxsize=1)`
/// names `lru_cache`.
pub fn decorator_name(decorator: &str) -> &str {
    let head = decorator.split('(').next().unwrap_or(decorator);
    head.rsplit('.').next().unwrap_or(head)
}

fn function_kind(decorators: &[String], is_in_class: bool) -> FunctionKind {
    let has = |wanted: &str| decorators.iter().any(|d| decorator_name(d) == wanted);
    if has("property") {
        FunctionKind::Property
    } else if has("staticmethod") {
        FunctionKind::Staticmethod
    } else if has("classmethod") {
        FunctionKind::Classmethod
    } else if is_in_class {
        FunctionKind::Method
    } else {
        FunctionKind::Function
    }
}

fn ann_assign_var(
    name: &str,
    ann: &ruff_python_ast::StmtAnnAssign,
    ctx: &Ctx<'_>,
) -> Result<VarRaw, PythonSyntaxError> {
    Ok(VarRaw {
        name: name.to_string(),
        var_type: ctx.unparse(&ann.annotation)?,
        value: ann
            .value
            .as_ref()
            .map(|v| ctx.unparse(v))
            .transpose()?
            .unwrap_or_default(),
    })
}

/// A leading underscore marks a name private by convention.
fn is_private(name: &str) -> bool {
    name.starts_with('_')
}

/// Whether a class member is its public surface: `__init__` always, any other
/// dunder only when it carries a docstring, a `_private` name never.
fn member_is_public(f: &StmtFunctionDef) -> bool {
    let name = f.name.as_str();
    if name == "__init__" {
        return true;
    }
    if name.len() > 4 && name.starts_with("__") && name.ends_with("__") {
        return get_docstring(&f.body).is_some();
    }
    !is_private(name)
}

/// One entry per name a scope publishes: `@overload` stubs give way to the
/// implementation (the first stub stands in when there is none), a
/// property's `@name.setter`/`@name.deleter` belong to its getter, and a
/// name defined twice is its last definition, as Python binds it.
fn one_per_name(functions: Vec<FunctionRaw>) -> Vec<FunctionRaw> {
    let is_overload =
        |f: &FunctionRaw| f.decorators.iter().any(|d| decorator_name(d) == "overload");
    let is_accessor = |f: &FunctionRaw| {
        ["setter", "deleter", "getter"].iter().any(|kind| {
            f.decorators
                .iter()
                .any(|d| *d == format!("{}.{kind}", f.name))
        })
    };
    let mut kept: Vec<FunctionRaw> = Vec::new();
    for (index, f) in functions.iter().enumerate() {
        if is_accessor(f) {
            continue;
        }
        let redefined = functions[index + 1..]
            .iter()
            .any(|later| later.name == f.name && !is_overload(later) && !is_accessor(later));
        if !is_overload(f) && redefined {
            continue;
        }
        if is_overload(f) {
            let implemented = functions
                .iter()
                .any(|other| other.name == f.name && !is_overload(other));
            let first_stub = functions[..index]
                .iter()
                .all(|other| other.name != f.name || !is_overload(other));
            if implemented || !first_stub {
                continue;
            }
        }
        kept.push(f.clone());
    }
    kept
}

fn extract_class_raw(node: &StmtClassDef, ctx: &Ctx<'_>) -> Result<ClassRaw, PythonSyntaxError> {
    let mut methods = Vec::new();
    let mut class_vars = Vec::new();
    let mut inner_classes = Vec::new();
    for item in &node.body {
        match item {
            Stmt::FunctionDef(f) if member_is_public(f) => {
                methods.push(extract_function_raw(f, ctx, true)?)
            }
            Stmt::AnnAssign(ann) => {
                if let Expr::Name(name) = ann.target.as_ref() {
                    if !is_private(name.id.as_str()) {
                        class_vars.push(ann_assign_var(name.id.as_str(), ann, ctx)?);
                    }
                }
            }
            // A plain assignment in a class body is a class attribute: an
            // enum member, a default, a constant.
            Stmt::Assign(assign) => {
                for target in &assign.targets {
                    let Expr::Name(name) = target else { continue };
                    if !is_private(name.id.as_str()) {
                        class_vars.push(VarRaw {
                            name: name.id.to_string(),
                            var_type: String::new(),
                            value: ctx.unparse(&assign.value)?,
                        });
                    }
                }
            }
            Stmt::ClassDef(c) if !is_private(c.name.as_str()) => {
                inner_classes.push(extract_class_raw(c, ctx)?)
            }
            _ => {}
        }
    }
    let methods = one_per_name(methods);
    let bases = match node.arguments.as_ref() {
        Some(args) => ctx.unparse_all(args.args.iter())?,
        None => Vec::new(),
    };
    Ok(ClassRaw {
        name: node.name.to_string(),
        bases,
        decorators: ctx.unparse_all(node.decorator_list.iter().map(|d| &d.expression))?,
        docstring_raw: get_docstring(&node.body),
        methods,
        class_vars,
        inner_classes,
        source_file: ctx.source_file.to_string(),
        line_number: ctx.keyword_line(node.range().start(), &node.decorator_list),
    })
}

/// Universal newlines and the BOM rejection of `compile()`.
fn prepare_source<'a>(
    source: &'a str,
    source_file: &str,
) -> Result<Cow<'a, str>, PythonSyntaxError> {
    if source.starts_with('\u{feff}') {
        return Err(PythonSyntaxError {
            path: PathBuf::from(source_file),
            message: "source code string cannot contain a UTF-8 BOM".to_string(),
            line: 1,
            column: 1,
            kind: ErrorKind::Syntax,
        });
    }
    if source.contains('\r') {
        Ok(Cow::Owned(source.replace("\r\n", "\n").replace('\r', "\n")))
    } else {
        Ok(Cow::Borrowed(source))
    }
}

fn check_paren_depth(tokens: &Tokens, ctx: &Ctx<'_>) -> Result<(), PythonSyntaxError> {
    let mut level = 0usize;
    for tok in tokens.iter() {
        match tok.kind() {
            TokenKind::Lpar | TokenKind::Lsqb | TokenKind::Lbrace => {
                if level >= MAX_PAREN_LEVEL {
                    return Err(ctx.error(
                        "too many nested parentheses",
                        tok.range().start(),
                        ErrorKind::Syntax,
                    ));
                }
                level += 1;
            }
            TokenKind::Rpar | TokenKind::Rsqb | TokenKind::Rbrace => {
                level = level.saturating_sub(1);
            }
            _ => {}
        }
    }
    Ok(())
}

/// Parse a Python source into the raw module tree; docstrings stay unparsed text.
pub fn parse_source_raw(
    source: &str,
    module_name: &str,
    source_file: &str,
) -> Result<ModuleRaw, PythonSyntaxError> {
    let source = prepare_source(source, source_file)?;
    let source = source.as_ref();
    let ctx = Ctx {
        source,
        source_file,
        line_index: LineIndex::new(source),
    };
    let parsed = parse_module(source)
        .map_err(|e| ctx.error(&e.error.to_string(), e.location.start(), ErrorKind::Syntax))?;
    check_paren_depth(parsed.tokens(), &ctx)?;
    let body = parsed.suite();

    // The last top-level `__all__ = [...]`/`(...)`, annotated or not, wins;
    // non-string elements are dropped.
    let is_all = |t: &Expr| matches!(t, Expr::Name(n) if n.id.as_str() == "__all__");
    let mut dunder_all: Option<Vec<String>> = None;
    for stmt in body {
        let value = match stmt {
            Stmt::Assign(assign) if assign.targets.iter().any(is_all) => assign.value.as_ref(),
            Stmt::AnnAssign(ann) if is_all(&ann.target) => match &ann.value {
                Some(value) => value.as_ref(),
                None => continue,
            },
            _ => continue,
        };
        match value {
            Expr::List(list) => dunder_all = Some(string_constants(&list.elts)),
            Expr::Tuple(tuple) => dunder_all = Some(string_constants(&tuple.elts)),
            _ => {}
        }
    }
    // `__all__` is the whole list when a module writes one; without it every
    // name but a `_private` one is public.
    let visible = |name: &str| match &dunder_all {
        Some(all) => all.iter().any(|s| s == name),
        None => !is_private(name),
    };

    let mut classes = Vec::new();
    let mut functions = Vec::new();
    let mut constants = Vec::new();
    for stmt in body {
        match stmt {
            Stmt::ClassDef(c) if visible(c.name.as_str()) => {
                classes.push(extract_class_raw(c, &ctx)?);
            }
            Stmt::FunctionDef(f) if visible(f.name.as_str()) => {
                functions.push(extract_function_raw(f, &ctx, false)?);
            }
            Stmt::AnnAssign(ann) => {
                if let Expr::Name(name) = ann.target.as_ref() {
                    if visible(name.id.as_str()) {
                        constants.push(ann_assign_var(name.id.as_str(), ann, &ctx)?);
                    }
                }
            }
            Stmt::Assign(assign) => {
                for target in &assign.targets {
                    let Expr::Name(name) = target else { continue };
                    let n = name.id.as_str();
                    if is_upper_name(n) && !n.starts_with('_') && visible(n) {
                        constants.push(VarRaw {
                            name: n.to_string(),
                            var_type: String::new(),
                            value: ctx.unparse(&assign.value)?,
                        });
                    }
                }
            }
            _ => {}
        }
    }

    Ok(ModuleRaw {
        name: module_name.to_string(),
        docstring_raw: get_docstring(body),
        classes,
        functions: one_per_name(functions),
        constants,
        source_file: source_file.to_string(),
    })
}

fn string_constants(elts: &[Expr]) -> Vec<String> {
    elts.iter()
        .filter_map(|e| match e {
            Expr::StringLiteral(s) => Some(s.value.to_str().to_string()),
            _ => None,
        })
        .collect()
}

/// Python `str.isupper()`: at least one cased character and no lowercase one.
fn is_upper_name(s: &str) -> bool {
    let mut has_upper = false;
    for ch in s.chars() {
        if ch.is_lowercase() {
            return false;
        }
        has_upper |= ch.is_uppercase();
    }
    has_upper
}

#[cfg(test)]
#[path = "extract_tests.rs"]
mod tests;
