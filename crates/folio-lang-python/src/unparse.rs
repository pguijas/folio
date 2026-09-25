//! CPython 3.12 `ast.unparse`-compatible expression renderer.
//!
//! Given a ruff `Expr`, produce the same string CPython 3.12's `ast.unparse` would.

use num_bigint::BigUint;
use std::cell::Cell;

use ruff_python_ast::{
    BoolOp, ConversionFlag, Expr, ExprAttribute, ExprAwait, ExprBinOp, ExprBoolOp,
    ExprBooleanLiteral, ExprBytesLiteral, ExprCall, ExprCompare, ExprDict, ExprDictComp,
    ExprFString, ExprGenerator, ExprIf, ExprLambda, ExprList, ExprListComp, ExprNamed,
    ExprNumberLiteral, ExprSet, ExprSetComp, ExprSlice, ExprStarred, ExprStringLiteral,
    ExprSubscript, ExprTuple, ExprUnaryOp, ExprYield, ExprYieldFrom, FStringPart, Int,
    InterpolatedStringElement, Number, Operator, UnaryOp,
};

// ---------------------------------------------------------------------------
// Precedence (mirrors CPython _Precedence enum)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
#[repr(u8)]
enum Prec {
    NamedExpr = 1,
    Tuple,
    Yield,
    Test, // default for most nodes
    Or,
    And,
    Not,
    Cmp,
    Expr, // = BOR
    Bxor,
    Band,
    Shift,
    Arith,
    Term,
    Factor,
    Power,
    Await,
    Atom,
}

impl Prec {
    fn next(self) -> Self {
        match self {
            Prec::NamedExpr => Prec::Tuple,
            Prec::Tuple => Prec::Yield,
            Prec::Yield => Prec::Test,
            Prec::Test => Prec::Or,
            Prec::Or => Prec::And,
            Prec::And => Prec::Not,
            Prec::Not => Prec::Cmp,
            Prec::Cmp => Prec::Expr,
            Prec::Expr => Prec::Bxor,
            Prec::Bxor => Prec::Band,
            Prec::Band => Prec::Shift,
            Prec::Shift => Prec::Arith,
            Prec::Arith => Prec::Term,
            Prec::Term => Prec::Factor,
            Prec::Factor => Prec::Power,
            Prec::Power => Prec::Await,
            Prec::Await => Prec::Atom,
            Prec::Atom => Prec::Atom,
        }
    }
}

fn binop_prec(op: Operator) -> Prec {
    match op {
        Operator::BitOr => Prec::Expr,
        Operator::BitXor => Prec::Bxor,
        Operator::BitAnd => Prec::Band,
        Operator::LShift | Operator::RShift => Prec::Shift,
        Operator::Add | Operator::Sub => Prec::Arith,
        Operator::Mult | Operator::MatMult | Operator::Div | Operator::FloorDiv | Operator::Mod => {
            Prec::Term
        }
        Operator::Pow => Prec::Power,
    }
}

fn unaryop_prec(op: UnaryOp) -> Prec {
    match op {
        UnaryOp::Not => Prec::Not,
        _ => Prec::Factor,
    }
}

// ---------------------------------------------------------------------------
// Core unparse
// ---------------------------------------------------------------------------

/// Maximum expression nesting the renderer accepts.
///
/// Every AST level costs a bounded number of Rust frames, so this keeps
/// stack use well under the smallest thread stack the extension runs on
/// (Windows' 1 MiB main thread, rayon's 2 MiB workers).  CPython's own
/// `ast.unparse` raises `RecursionError` at roughly a third of
/// `sys.getrecursionlimit()` (default 1000), so anything this deep already
/// fails in CPython.
pub const MAX_DEPTH: usize = 1000;

/// Why an expression could not be rendered.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UnparseError {
    /// The expression nests deeper than [`MAX_DEPTH`].
    TooDeep,
}

struct Unparser {
    /// Current nesting depth of `unparse` calls.
    depth: Cell<usize>,
    /// Set once the depth guard trips; the partial output is discarded.
    too_deep: Cell<bool>,
}

impl Unparser {
    fn new(_source: &str) -> Self {
        Self {
            depth: Cell::new(0),
            too_deep: Cell::new(false),
        }
    }

    fn unparse(&self, expr: &Expr, prec: Prec) -> String {
        if self.depth.get() >= MAX_DEPTH {
            self.too_deep.set(true);
            return String::new();
        }
        self.depth.set(self.depth.get() + 1);
        let (s, own_prec) = self.unparse_inner(expr);
        self.depth.set(self.depth.get() - 1);
        if own_prec < prec {
            format!("({})", s)
        } else {
            s
        }
    }

    fn unparse_inner(&self, expr: &Expr) -> (String, Prec) {
        match expr {
            Expr::BoolOp(e) => self.visit_bool_op(e),
            Expr::Named(e) => self.visit_named(e),
            Expr::BinOp(e) => self.visit_bin_op(e),
            Expr::UnaryOp(e) => self.visit_unary_op(e),
            Expr::Lambda(e) => self.visit_lambda(e),
            Expr::If(e) => self.visit_if(e),
            Expr::Dict(e) => self.visit_dict(e),
            Expr::Set(e) => self.visit_set(e),
            Expr::ListComp(e) => self.visit_list_comp(e),
            Expr::SetComp(e) => self.visit_set_comp(e),
            Expr::DictComp(e) => self.visit_dict_comp(e),
            Expr::Generator(e) => self.visit_generator(e),
            Expr::Await(e) => self.visit_await(e),
            Expr::Yield(e) => self.visit_yield(e),
            Expr::YieldFrom(e) => self.visit_yield_from(e),
            Expr::Compare(e) => self.visit_compare(e),
            Expr::Call(e) => self.visit_call(e),
            Expr::FString(e) => self.visit_fstring(e),
            Expr::StringLiteral(e) => self.visit_string_literal(e),
            Expr::BytesLiteral(e) => self.visit_bytes_literal(e),
            Expr::NumberLiteral(e) => self.visit_number_literal(e),
            Expr::BooleanLiteral(e) => self.visit_boolean_literal(e),
            Expr::NoneLiteral(_) => (String::from("None"), Prec::Atom),
            Expr::EllipsisLiteral(_) => (String::from("..."), Prec::Atom),
            Expr::Attribute(e) => self.visit_attribute(e),
            Expr::Subscript(e) => self.visit_subscript(e),
            Expr::Starred(e) => self.visit_starred(e),
            Expr::Name(e) => (e.id.to_string(), Prec::Atom),
            Expr::List(e) => self.visit_list(e),
            Expr::Tuple(e) => self.visit_tuple(e),
            Expr::Slice(e) => self.visit_slice(e),
            Expr::TString(_) | Expr::IpyEscapeCommand(_) => {
                // TString (Python 3.14+) and IPython not in CPython 3.12
                (String::new(), Prec::Atom)
            }
        }
    }

    // ----- Literals -----

    fn visit_string_literal(&self, e: &ExprStringLiteral) -> (String, Prec) {
        // After parsing, implicitly concatenated parts are merged into one value.
        let s = e.value.to_str();
        let is_unicode = e.value.is_unicode();
        let r = repr_str(s);
        if is_unicode {
            (format!("u{}", r), Prec::Atom)
        } else {
            (r, Prec::Atom)
        }
    }

    fn visit_bytes_literal(&self, e: &ExprBytesLiteral) -> (String, Prec) {
        // Collect all bytes from all parts
        let bytes: Vec<u8> = e.value.bytes().collect();
        (repr_bytes(&bytes), Prec::Atom)
    }

    fn visit_number_literal(&self, e: &ExprNumberLiteral) -> (String, Prec) {
        let s = match &e.value {
            Number::Int(i) => repr_int(i),
            Number::Float(f) => repr_float(*f),
            Number::Complex { real: _, imag } => repr_complex_imag(*imag),
        };
        (s, Prec::Atom)
    }

    fn visit_boolean_literal(&self, e: &ExprBooleanLiteral) -> (String, Prec) {
        (
            if e.value { "True" } else { "False" }.to_string(),
            Prec::Atom,
        )
    }

    // ----- Operators -----

    fn visit_bool_op(&self, e: &ExprBoolOp) -> (String, Prec) {
        let prec = match e.op {
            BoolOp::And => Prec::And,
            BoolOp::Or => Prec::Or,
        };
        let op_str = e.op.as_str();
        // CPython uses increasing_level_traverse: each operand gets an
        // increasingly higher precedence requirement.
        let mut level = prec;
        let parts: Vec<String> = e
            .values
            .iter()
            .map(|v| {
                level = level.next();
                self.unparse(v, level)
            })
            .collect();
        (parts.join(&format!(" {} ", op_str)), prec)
    }

    fn visit_named(&self, e: &ExprNamed) -> (String, Prec) {
        let target = self.unparse(&e.target, Prec::NamedExpr);
        let value = self.unparse(&e.value, Prec::NamedExpr);
        (format!("{} := {}", target, value), Prec::NamedExpr)
    }

    fn visit_bin_op(&self, e: &ExprBinOp) -> (String, Prec) {
        let prec = binop_prec(e.op);
        let left_prec = if e.op == Operator::Pow {
            prec.next()
        } else {
            prec
        };
        let right_prec = if e.op == Operator::Pow {
            prec
        } else {
            prec.next()
        };
        let left = self.unparse(&e.left, left_prec);
        let right = self.unparse(&e.right, right_prec);
        (format!("{} {} {}", left, e.op.as_str(), right), prec)
    }

    fn visit_unary_op(&self, e: &ExprUnaryOp) -> (String, Prec) {
        let prec = unaryop_prec(e.op);
        let operand = self.unparse(&e.operand, prec);
        let s = match e.op {
            UnaryOp::Not => format!("not {}", operand),
            _ => format!("{}{}", e.op.as_str(), operand),
        };
        (s, prec)
    }

    /// Render a lambda expression.
    ///
    /// Uses CPython 3.11+ spacing: `lambda: x` (no space before colon when
    /// there are no parameters).  CPython 3.10 emitted `lambda : x`; the Rust
    /// renderer targets 3.11+ because the destination is a Python-free binary.
    fn visit_lambda(&self, e: &ExprLambda) -> (String, Prec) {
        let params = if let Some(params) = &e.parameters {
            self.format_params(params)
        } else {
            String::new()
        };
        let body = self.unparse(&e.body, Prec::Test);
        if params.is_empty() {
            (format!("lambda: {}", body), Prec::Test)
        } else {
            (format!("lambda {}: {}", params, body), Prec::Test)
        }
    }

    fn visit_if(&self, e: &ExprIf) -> (String, Prec) {
        let body = self.unparse(&e.body, Prec::Test.next());
        let test = self.unparse(&e.test, Prec::Test.next());
        let orelse = self.unparse(&e.orelse, Prec::Test);
        (format!("{} if {} else {}", body, test, orelse), Prec::Test)
    }

    // ----- Collections -----

    fn visit_dict(&self, e: &ExprDict) -> (String, Prec) {
        let items: Vec<String> = e
            .items
            .iter()
            .map(|item| {
                if let Some(key) = &item.key {
                    let k = self.unparse(key, Prec::Test);
                    let v = self.unparse(&item.value, Prec::Test);
                    format!("{}: {}", k, v)
                } else {
                    format!("**{}", self.unparse(&item.value, Prec::Expr))
                }
            })
            .collect();
        (format!("{{{}}}", items.join(", ")), Prec::Atom)
    }

    fn visit_set(&self, e: &ExprSet) -> (String, Prec) {
        let items: Vec<String> = e.elts.iter().map(|v| self.unparse(v, Prec::Test)).collect();
        (format!("{{{}}}", items.join(", ")), Prec::Atom)
    }

    fn visit_list(&self, e: &ExprList) -> (String, Prec) {
        let items: Vec<String> = e.elts.iter().map(|v| self.unparse(v, Prec::Test)).collect();
        (format!("[{}]", items.join(", ")), Prec::Atom)
    }

    fn visit_tuple(&self, e: &ExprTuple) -> (String, Prec) {
        if e.elts.is_empty() {
            return (String::from("()"), Prec::Atom);
        }
        let items: Vec<String> = e.elts.iter().map(|v| self.unparse(v, Prec::Test)).collect();
        if items.len() == 1 {
            (format!("({},)", items[0]), Prec::Atom)
        } else {
            (items.join(", "), Prec::Tuple)
        }
    }

    // ----- Comprehensions -----

    /// Render a comprehension clause (`for target in iter [if cond]`).
    ///
    /// Tuple targets are emitted bare: `for k, v in ...` (CPython 3.11+).
    /// CPython 3.10 parenthesised them: `for (k, v) in ...`.  This renderer
    /// targets 3.11+.
    fn format_comprehension(&self, comp: &ruff_python_ast::Comprehension) -> String {
        let target = self.unparse(&comp.target, Prec::Tuple);
        let iter = self.unparse(&comp.iter, Prec::Test.next());
        let ifs: String = comp
            .ifs
            .iter()
            .map(|i| format!(" if {}", self.unparse(i, Prec::Test.next())))
            .collect();
        let async_str = if comp.is_async { " async" } else { "" };
        format!("{} for {} in {}{}", async_str, target, iter, ifs)
    }

    fn visit_list_comp(&self, e: &ExprListComp) -> (String, Prec) {
        let elt = self.unparse(&e.elt, Prec::Test);
        let gens: String = e
            .generators
            .iter()
            .map(|g| self.format_comprehension(g))
            .collect();
        (format!("[{}{}]", elt, gens), Prec::Atom)
    }

    fn visit_set_comp(&self, e: &ExprSetComp) -> (String, Prec) {
        let elt = self.unparse(&e.elt, Prec::Test);
        let gens: String = e
            .generators
            .iter()
            .map(|g| self.format_comprehension(g))
            .collect();
        (format!("{{{}{}}}", elt, gens), Prec::Atom)
    }

    fn visit_dict_comp(&self, e: &ExprDictComp) -> (String, Prec) {
        let k = e
            .key
            .as_ref()
            .map(|k| self.unparse(k, Prec::Test))
            .unwrap_or_default();
        let v = self.unparse(&e.value, Prec::Test);
        let gens: String = e
            .generators
            .iter()
            .map(|g| self.format_comprehension(g))
            .collect();
        (format!("{{{}: {}{}}}", k, v, gens), Prec::Atom)
    }

    fn visit_generator(&self, e: &ExprGenerator) -> (String, Prec) {
        let elt = self.unparse(&e.elt, Prec::Test);
        let gens: String = e
            .generators
            .iter()
            .map(|g| self.format_comprehension(g))
            .collect();
        // GeneratorExp is always parenthesised in CPython unparse
        (format!("({}{})", elt, gens), Prec::Atom)
    }

    // ----- Await / Yield -----

    fn visit_await(&self, e: &ExprAwait) -> (String, Prec) {
        let value = self.unparse(&e.value, Prec::Atom);
        (format!("await {}", value), Prec::Await)
    }

    fn visit_yield(&self, e: &ExprYield) -> (String, Prec) {
        if let Some(value) = &e.value {
            let v = self.unparse(value, Prec::Test);
            (format!("(yield {})", v), Prec::Atom)
        } else {
            (String::from("(yield)"), Prec::Atom)
        }
    }

    fn visit_yield_from(&self, e: &ExprYieldFrom) -> (String, Prec) {
        let v = self.unparse(&e.value, Prec::Test);
        (format!("(yield from {})", v), Prec::Atom)
    }

    // ----- Compare -----

    fn visit_compare(&self, e: &ExprCompare) -> (String, Prec) {
        let left = self.unparse(&e.left, Prec::Cmp.next());
        let mut s = left;
        for (op, comparator) in e.ops.iter().zip(e.comparators.iter()) {
            let c = self.unparse(comparator, Prec::Cmp.next());
            s = format!("{} {} {}", s, op.as_str(), c);
        }
        (s, Prec::Cmp)
    }

    // ----- Call -----

    fn visit_call(&self, e: &ExprCall) -> (String, Prec) {
        let func = self.unparse(&e.func, Prec::Atom);
        // Reorder: in CPython ast.unparse, positional args (incl. Starred) come first,
        // then keyword args. The Call node in ast has args and keywords separate,
        // but CPython unparse writes args in source order then keywords.
        // Ruff's ExprCall stores arguments differently:
        let args = &e.arguments;

        // Collect positional args (including Starred)
        let mut parts: Vec<String> = Vec::new();
        // First pass: non-keyword positional args
        for arg in &args.args {
            parts.push(self.unparse(arg, Prec::Test));
        }
        // Keywords
        for kw in &args.keywords {
            if let Some(id) = &kw.arg {
                parts.push(format!("{}={}", id, self.unparse(&kw.value, Prec::Test)));
            } else {
                parts.push(format!("**{}", self.unparse(&kw.value, Prec::Expr)));
            }
        }
        (format!("{}({})", func, parts.join(", ")), Prec::Atom)
    }

    // ----- Attribute / Subscript -----

    fn visit_attribute(&self, e: &ExprAttribute) -> (String, Prec) {
        let value = self.unparse(&e.value, Prec::Atom);
        // CPython adds a space after int-literal receiver: `1 .real`
        let needs_space = self.is_int_literal(&e.value);
        if needs_space {
            (format!("{} .{}", value, e.attr), Prec::Atom)
        } else {
            (format!("{}.{}", value, e.attr), Prec::Atom)
        }
    }

    fn is_int_literal(&self, expr: &Expr) -> bool {
        matches!(expr, Expr::NumberLiteral(n) if matches!(n.value, Number::Int(_)))
    }

    fn visit_subscript(&self, e: &ExprSubscript) -> (String, Prec) {
        let value = self.unparse(&e.value, Prec::Atom);
        let slice = self.unparse_slice(&e.slice);
        (format!("{}[{}]", value, slice), Prec::Atom)
    }

    fn unparse_slice(&self, expr: &Expr) -> String {
        match expr {
            Expr::Tuple(t) if !t.elts.is_empty() => {
                // In subscripts, tuples drop their parens
                let items: Vec<String> =
                    t.elts.iter().map(|e| self.unparse_slice_item(e)).collect();
                // Keep trailing comma for 1-element tuples in subscript context
                if items.len() == 1 {
                    format!("{},", items[0])
                } else {
                    items.join(", ")
                }
            }
            _ => self.unparse_slice_item(expr),
        }
    }

    fn unparse_slice_item(&self, expr: &Expr) -> String {
        match expr {
            Expr::Slice(s) => self.format_slice(s),
            Expr::Starred(s) => {
                // Starred in subscript context; trailing comma handled by tuple logic
                format!("*{}", self.unparse(&s.value, Prec::Test))
            }
            _ => self.unparse(expr, Prec::Test),
        }
    }

    fn format_slice(&self, s: &ExprSlice) -> String {
        let lower = s
            .lower
            .as_ref()
            .map(|l| self.unparse(l, Prec::Test))
            .unwrap_or_default();
        let upper = s
            .upper
            .as_ref()
            .map(|u| self.unparse(u, Prec::Test))
            .unwrap_or_default();
        if let Some(step) = &s.step {
            let step_str = self.unparse(step, Prec::Test);
            format!("{}:{}:{}", lower, upper, step_str)
        } else {
            format!("{}:{}", lower, upper)
        }
    }

    fn visit_starred(&self, e: &ExprStarred) -> (String, Prec) {
        let value = self.unparse(&e.value, Prec::Expr);
        (format!("*{}", value), Prec::Atom)
    }

    fn visit_slice(&self, e: &ExprSlice) -> (String, Prec) {
        (self.format_slice(e), Prec::Atom)
    }

    // ----- F-strings -----

    fn visit_fstring(&self, e: &ExprFString) -> (String, Prec) {
        // Phase 1: collect rendered parts. Each is (text, is_constant).
        // Matches CPython's visit_JoinedStr approach.
        let mut fstring_parts: Vec<(String, bool)> = Vec::new();

        for part in e.value.as_slice() {
            match part {
                FStringPart::Literal(lit) => {
                    // Plain string literal concatenated with the f-string.
                    // Must escape braces since we're merging into an f-string.
                    let text = lit.value.replace('{', "{{").replace('}', "}}");
                    fstring_parts.push((text, true));
                }
                FStringPart::FString(fs) => {
                    for element in &fs.elements {
                        match element {
                            InterpolatedStringElement::Literal(lit) => {
                                // Literal inside f-string: escape braces
                                let text = lit.value.replace('{', "{{").replace('}', "}}");
                                fstring_parts.push((text, true));
                            }
                            InterpolatedStringElement::Interpolation(interp) => {
                                // Debug text (f'{x=}' -> 'x={x!r}'): the debug
                                // literal = leading + unparse(expr) + trailing,
                                // emitted OUTSIDE the braces as constant text.
                                if let Some(debug) = &interp.debug_text {
                                    let expr_text =
                                        self.unparse(&interp.expression, Prec::Test.next());
                                    let dbg_lit = format!(
                                        "{}{}{}",
                                        debug.leading(),
                                        expr_text,
                                        debug.trailing()
                                    );
                                    fstring_parts.push((dbg_lit, true));
                                }
                                // Expression part
                                let mut expr_text = String::from("{");
                                expr_text
                                    .push_str(&self.format_fstring_interpolation_inner(interp));
                                expr_text.push('}');
                                fstring_parts.push((expr_text, false));
                            }
                        }
                    }
                }
            }
        }

        // Phase 2: Quote selection matching CPython's algorithm.
        // _ALL_QUOTES = ("'", '"', '"""', "'''")
        let all_quotes: Vec<&str> = vec!["'", "\"", "\"\"\"", "'''"];
        let mut quote_types: Vec<&str> = all_quotes.clone();
        let mut new_fstring_parts: Vec<String> = Vec::new();
        let mut fallback_to_repr = false;

        for (value, is_constant) in &fstring_parts {
            if *is_constant {
                // For constant parts, use _str_literal_helper logic
                let (escaped, new_qt) = fstring_str_literal_helper(value, &quote_types);
                // Check if new_qt is disjoint with quote_types
                if new_qt.iter().all(|q| !quote_types.contains(q)) {
                    fallback_to_repr = true;
                    break;
                }
                quote_types = new_qt;
                new_fstring_parts.push(escaped);
            } else {
                // Expression part: if it contains \n, restrict to triple quotes
                if value.contains('\n') {
                    quote_types.retain(|q| q.len() == 3);
                }
                // Remove quote types that appear in expression text
                let filtered: Vec<&str> = quote_types
                    .iter()
                    .filter(|q| !value.contains(**q))
                    .copied()
                    .collect();
                if !filtered.is_empty() {
                    quote_types = filtered;
                }
                new_fstring_parts.push(value.clone());
            }
        }

        if fallback_to_repr {
            // Fallback: use ''' with repr-based escaping of constants
            quote_types = vec!["'''"];
            new_fstring_parts.clear();
            for (value, is_constant) in &fstring_parts {
                if *is_constant {
                    // Force repr to use single quotes by prepending "
                    let forced = format!("\"{}", value);
                    let r = repr_str(&forced);
                    // repr gives us '\"...' or "\"..." - we need to strip
                    // the outer quotes and the leading \"
                    let expected_prefix = "'\"";
                    if r.starts_with(expected_prefix) {
                        let inner = &r[expected_prefix.len()..r.len() - 1];
                        new_fstring_parts.push(inner.to_string());
                    } else {
                        new_fstring_parts.push(value.clone());
                    }
                } else {
                    new_fstring_parts.push(value.clone());
                }
            }
        }

        let combined: String = new_fstring_parts.concat();
        let quote = quote_types[0];
        let result = format!("f{}{}{}", quote, combined, quote);
        (result, Prec::Atom)
    }

    /// Format the INSIDE of an f-string interpolation `{...}` (without outer braces).
    /// For debug expressions, the conversion defaults to `!r` when none is specified.
    fn format_fstring_interpolation_inner(
        &self,
        interp: &ruff_python_ast::InterpolatedElement,
    ) -> String {
        let mut s = String::new();

        // The expression inside braces
        let expr_str = self.unparse(&interp.expression, Prec::Test.next());
        s.push_str(&expr_str);

        // Conversion flag
        // For debug expressions (f'{x=}'), CPython defaults to !r when no explicit
        // conversion is specified.
        let has_debug = interp.debug_text.is_some();
        let has_format_spec = interp.format_spec.is_some();
        match interp.conversion {
            ConversionFlag::Str => s.push_str("!s"),
            ConversionFlag::Repr => s.push_str("!r"),
            ConversionFlag::Ascii => s.push_str("!a"),
            ConversionFlag::None => {
                // CPython adds !r for debug expressions only when there is
                // no explicit conversion AND no format spec.
                if has_debug && !has_format_spec {
                    s.push_str("!r");
                }
            }
        }

        // Format spec
        if let Some(spec) = &interp.format_spec {
            s.push(':');
            for element in &spec.elements {
                match element {
                    InterpolatedStringElement::Literal(lit) => {
                        // Escape newlines etc. in format spec literals
                        s.push_str(&escape_fstring_format_spec(&lit.value));
                    }
                    InterpolatedStringElement::Interpolation(inner) => {
                        s.push('{');
                        s.push_str(&self.format_fstring_interpolation_inner(inner));
                        s.push('}');
                    }
                }
            }
        }

        s
    }

    // ----- Parameters -----

    fn format_params(&self, params: &ruff_python_ast::Parameters) -> String {
        let mut parts: Vec<String> = Vec::new();

        for p in &params.posonlyargs {
            parts.push(self.format_param_with_default(p));
        }
        if !params.posonlyargs.is_empty() {
            parts.push(String::from("/"));
        }

        for p in &params.args {
            parts.push(self.format_param_with_default(p));
        }

        if let Some(vararg) = &params.vararg {
            let ann = vararg
                .annotation
                .as_ref()
                .map(|a| format!(": {}", self.unparse(a, Prec::Test)))
                .unwrap_or_default();
            parts.push(format!("*{}{}", vararg.name, ann));
        } else if !params.kwonlyargs.is_empty() {
            parts.push(String::from("*"));
        }

        for p in &params.kwonlyargs {
            parts.push(self.format_param_with_default(p));
        }

        if let Some(kwarg) = &params.kwarg {
            let ann = kwarg
                .annotation
                .as_ref()
                .map(|a| format!(": {}", self.unparse(a, Prec::Test)))
                .unwrap_or_default();
            parts.push(format!("**{}{}", kwarg.name, ann));
        }

        parts.join(", ")
    }

    fn format_param_with_default(&self, pwd: &ruff_python_ast::ParameterWithDefault) -> String {
        let name = pwd.parameter.name.as_str();
        let ann = pwd
            .parameter
            .annotation
            .as_ref()
            .map(|a| format!(": {}", self.unparse(a, Prec::Test)))
            .unwrap_or_default();
        let default = pwd
            .default
            .as_ref()
            .map(|d| format!("={}", self.unparse(d, Prec::Test)))
            .unwrap_or_default();
        if ann.is_empty() {
            format!("{}{}", name, default)
        } else {
            format!("{}{}{}", name, ann, default)
        }
    }
}

// ---------------------------------------------------------------------------
// repr functions matching CPython 3.12
// ---------------------------------------------------------------------------

/// Python `repr(str)`: single-quotes unless contains `'` but not `"`
pub fn repr_str(s: &str) -> String {
    let has_single = s.contains('\'');
    let has_double = s.contains('"');
    let quote = if has_single && !has_double { '"' } else { '\'' };
    let mut out = String::with_capacity(s.len() + 2);
    out.push(quote);
    for ch in s.chars() {
        if ch == quote {
            out.push('\\');
            out.push(ch);
        } else if ch == '\\' {
            out.push_str("\\\\");
        } else if ch == '\n' {
            out.push_str("\\n");
        } else if ch == '\t' {
            out.push_str("\\t");
        } else if ch == '\r' {
            out.push_str("\\r");
        } else if !is_printable(ch) {
            // Escape non-printable characters
            let cp = ch as u32;
            if cp < 0x100 {
                out.push_str(&format!("\\x{:02x}", cp));
            } else if cp < 0x10000 {
                out.push_str(&format!("\\u{:04x}", cp));
            } else {
                out.push_str(&format!("\\U{:08x}", cp));
            }
        } else {
            out.push(ch);
        }
    }
    out.push(quote);
    out
}

/// Python `repr(bytes)`: same quote rule, specific byte escaping
fn repr_bytes(bytes: &[u8]) -> String {
    let has_single = bytes.contains(&b'\'');
    let has_double = bytes.contains(&b'"');
    let quote = if has_single && !has_double {
        b'"'
    } else {
        b'\''
    };
    let mut out = String::from("b");
    out.push(quote as char);
    for &b in bytes {
        if b == quote {
            out.push('\\');
            out.push(b as char);
        } else if b == b'\\' {
            out.push_str("\\\\");
        } else if b == b'\t' {
            out.push_str("\\t");
        } else if b == b'\n' {
            out.push_str("\\n");
        } else if b == b'\r' {
            out.push_str("\\r");
        } else if !(0x20..0x7f).contains(&b) {
            out.push_str(&format!("\\x{:02x}", b));
        } else {
            out.push(b as char);
        }
    }
    out.push(quote as char);
    out
}

/// repr(int) in decimal
fn repr_int(i: &Int) -> String {
    if let Some(val) = i.as_u64() {
        return val.to_string();
    }
    // Big int: the Display impl gives us the token text (could be hex, octal, etc.)
    let token = i.to_string();
    // Parse to BigUint and convert to decimal
    big_int_to_decimal(&token)
}

fn big_int_to_decimal(token: &str) -> String {
    let s = token.replace('_', "");
    if let Some(hex) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        BigUint::parse_bytes(hex.as_bytes(), 16)
            .map(|n| n.to_string())
            .unwrap_or_else(|| s.clone())
    } else if let Some(oct) = s.strip_prefix("0o").or_else(|| s.strip_prefix("0O")) {
        BigUint::parse_bytes(oct.as_bytes(), 8)
            .map(|n| n.to_string())
            .unwrap_or_else(|| s.clone())
    } else if let Some(bin) = s.strip_prefix("0b").or_else(|| s.strip_prefix("0B")) {
        BigUint::parse_bytes(bin.as_bytes(), 2)
            .map(|n| n.to_string())
            .unwrap_or_else(|| s.clone())
    } else {
        // Already decimal, just parse and print (removes underscores)
        BigUint::parse_bytes(s.as_bytes(), 10)
            .map(|n| n.to_string())
            .unwrap_or_else(|| s.clone())
    }
}

/// repr(float) matching CPython 3.12
/// Uses shortest round-trip representation.
/// Exponent form if decimal exponent < -4 or >= 16.
fn repr_float(f: f64) -> String {
    if f.is_infinite() {
        return if f > 0.0 {
            "1e309".to_string()
        } else {
            "-1e309".to_string()
        };
    }
    if f.is_nan() {
        // nan only from folded constants; unlikely in unparse
        return "float('nan')".to_string();
    }

    // Check if it's -0.0
    if f == 0.0 && f.is_sign_negative() {
        return "-0.0".to_string();
    }

    // Python uses exponent form when decimal exponent < -4 or >= 16
    python_float_format(f)
}

fn python_float_format(f: f64) -> String {
    if f == 0.0 {
        return if f.is_sign_negative() {
            "-0.0".to_string()
        } else {
            "0.0".to_string()
        };
    }
    if f.is_infinite() {
        return if f > 0.0 {
            "1e309".to_string()
        } else {
            "-1e309".to_string()
        };
    }

    let sign = if f.is_sign_negative() { "-" } else { "" };
    let abs = f.abs();

    // Get the shortest round-trip representation
    // Rust's Debug format gives shortest digits
    let raw = format!("{:?}", abs);

    // Parse to figure out the decimal exponent
    // The raw format is either like "1234.0" or "1.234e5"
    let (_mantissa_str, dec_exp) = if let Some(pos) = raw.find('e') {
        let mant = &raw[..pos];
        let exp: i32 = raw[pos + 1..].parse().unwrap_or(0);
        // Normalize: mantissa is like "1.234", so decimal exp = exp
        let dot_pos = mant
            .find('.')
            .map(|p| p as i32)
            .unwrap_or(mant.len() as i32);
        let digits: String = mant.chars().filter(|c| c.is_ascii_digit()).collect();
        let actual_exp = exp + dot_pos - 1;
        (digits, actual_exp)
    } else {
        let dot_pos = raw.find('.').map(|p| p as i32).unwrap_or(raw.len() as i32);
        let digits: String = raw.chars().filter(|c| c.is_ascii_digit()).collect();
        // Trim trailing zeros after the dot for the count
        let trimmed = digits.trim_end_matches('0');
        let actual_exp = dot_pos - 1;
        let _ = trimmed; // We use the full digit string for formatting
        (digits, actual_exp)
    };

    // Python's rule: use exponent form if dec_exp < -4 or dec_exp >= 16
    if !(-4..16).contains(&dec_exp) {
        // Exponent notation
        format_python_exponent(sign, abs)
    } else {
        // Fixed notation
        format_python_fixed(sign, abs)
    }
}

fn format_python_exponent(sign: &str, abs: f64) -> String {
    // Use Python-style exponent: {m}e{+/-}{exp:02}
    // where m has no trailing zeros (except ensure at least one digit after potential dot)
    let raw = format!("{:e}", abs);
    // raw is like "1.23456e5" or "1e5"
    if let Some(epos) = raw.find('e') {
        let mant = &raw[..epos];
        let exp: i32 = raw[epos + 1..].parse().unwrap_or(0);

        // Remove trailing zeros from mantissa
        let mant_clean = if mant.contains('.') {
            mant.trim_end_matches('0').trim_end_matches('.')
        } else {
            mant
        };

        let exp_sign = if exp >= 0 { "+" } else { "-" };
        let exp_abs = exp.unsigned_abs();
        format!("{}{}e{}{:02}", sign, mant_clean, exp_sign, exp_abs)
    } else {
        format!("{}{}", sign, raw)
    }
}

fn format_python_fixed(sign: &str, abs: f64) -> String {
    // Fixed notation, need to ensure trailing .0
    // Use enough precision
    let s = format!("{}", abs);
    if s.contains('.') {
        format!("{}{}", sign, s)
    } else {
        format!("{}{}.0", sign, s)
    }
}

/// repr for the imaginary part of a complex literal
fn repr_complex_imag(imag: f64) -> String {
    if imag.is_infinite() {
        return if imag > 0.0 {
            "1e309j".to_string()
        } else {
            "-1e309j".to_string()
        };
    }

    // For complex imaginary, integral values print without .0
    // e.g., 1j not 1.0j, but 1.5j
    if imag == imag.trunc() && !imag.is_nan() && imag.abs() < 1e16 {
        // Integer-like
        let i = imag as i64;
        format!("{}j", i)
    } else {
        format!("{}j", repr_float(imag))
    }
}

// ---------------------------------------------------------------------------
// str.isprintable() - CPython 3.12 Unicode 15.0
// ---------------------------------------------------------------------------

/// Matches CPython `str.isprintable()`: returns false for categories
/// Cc, Cf, Cs, Co, Cn, Zl, Zp, Zs (except U+0020 space).
///
/// Uses the `unicode-general-category` crate for a real Unicode category table.
/// The crate's Unicode version may differ slightly from CPython 3.12's Unicode 15.0;
/// differences are limited to newly assigned code points between Unicode versions.
fn is_printable(ch: char) -> bool {
    if ch == ' ' {
        return true;
    }
    use unicode_general_category::{get_general_category, GeneralCategory};
    !matches!(
        get_general_category(ch),
        GeneralCategory::Control // Cc
            | GeneralCategory::Format // Cf
            | GeneralCategory::Surrogate // Cs
            | GeneralCategory::PrivateUse // Co
            | GeneralCategory::Unassigned // Cn
            | GeneralCategory::LineSeparator // Zl
            | GeneralCategory::ParagraphSeparator // Zp
            | GeneralCategory::SpaceSeparator // Zs
    )
}

// ---------------------------------------------------------------------------
// F-string quote selection
// ---------------------------------------------------------------------------

/// Mirrors CPython's `_str_literal_helper` with `escape_special_whitespace=True`.
/// Returns (escaped_string, possible_quote_types).
fn fstring_str_literal_helper<'a>(string: &str, quote_types: &[&'a str]) -> (String, Vec<&'a str>) {
    // escape_special_whitespace=True: escape \n and \t
    let mut escaped = String::with_capacity(string.len());
    for ch in string.chars() {
        if ch == '\\' || !ch.is_ascii() && !is_printable(ch) {
            // Use unicode_escape encoding
            let cp = ch as u32;
            if ch == '\\' {
                escaped.push_str("\\\\");
            } else if cp < 0x100 {
                escaped.push_str(&format!("\\x{:02x}", cp));
            } else if cp < 0x10000 {
                escaped.push_str(&format!("\\u{:04x}", cp));
            } else {
                escaped.push_str(&format!("\\U{:08x}", cp));
            }
        } else if ch == '\n' {
            escaped.push_str("\\n");
        } else if ch == '\t' {
            escaped.push_str("\\t");
        } else if ch == '\r' {
            escaped.push_str("\\r");
        } else if !is_printable(ch) {
            let cp = ch as u32;
            if cp < 0x100 {
                escaped.push_str(&format!("\\x{:02x}", cp));
            } else if cp < 0x10000 {
                escaped.push_str(&format!("\\u{:04x}", cp));
            } else {
                escaped.push_str(&format!("\\U{:08x}", cp));
            }
        } else {
            escaped.push(ch);
        }
    }

    let mut possible: Vec<&str> = if escaped.contains('\n') {
        // After escaping, if still contains \n (shouldn't with escape_special_whitespace)
        quote_types
            .iter()
            .filter(|q| q.len() == 3)
            .copied()
            .collect()
    } else {
        quote_types.to_vec()
    };

    possible.retain(|q| !escaped.contains(*q));

    if possible.is_empty() {
        // Fallback to repr on the original string
        let r = repr_str(string);
        // Try to pick a quote from quote_types
        let first_char = &r[0..1];
        let quote = quote_types
            .iter()
            .find(|q| q.starts_with(first_char))
            .unwrap_or(&quote_types[0]);
        let inner = &r[1..r.len() - 1];
        return (inner.to_string(), vec![*quote]);
    }

    if let Some(last_char) = escaped.chars().last() {
        // Sort so that we prefer '''"''' over """\""""
        // i.e., prefer a quote whose first char != last char of escaped_string
        possible.sort_by_key(|q| q.starts_with(last_char) as u8);
        // If we're using triple quotes and the last char matches, escape it
        if let Some(&q) = possible.first() {
            if q.starts_with(last_char) && q.len() == 3 {
                escaped.pop();
                escaped.push('\\');
                escaped.push(last_char);
            }
        }
    }

    (escaped, possible)
}

fn escape_fstring_format_spec(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for ch in text.chars() {
        match ch {
            // Braces in format specs are NOT escaped (they can contain nested interps)
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\t' => out.push_str("\\t"),
            '\r' => out.push_str("\\r"),
            _ => out.push(ch),
        }
    }
    out
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Unparse an expression to a string matching CPython 3.12 `ast.unparse`.
///
/// Fails with [`UnparseError::TooDeep`] instead of overflowing the stack
/// when the expression nests deeper than [`MAX_DEPTH`].
pub fn try_unparse_expr(expr: &Expr, source: &str) -> Result<String, UnparseError> {
    let u = Unparser::new(source);
    let rendered = u.unparse(expr, Prec::Test);
    if u.too_deep.get() {
        Err(UnparseError::TooDeep)
    } else {
        Ok(rendered)
    }
}

#[cfg(test)]
#[path = "unparse_tests.rs"]
mod tests;
