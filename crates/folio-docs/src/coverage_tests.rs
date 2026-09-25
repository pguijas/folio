use super::*;
use crate::fixtures::{class, doc, function, module};
use folio_ir::{ClassIR, FunctionIR, ModuleIR};

fn func(name: &str, documented: bool) -> FunctionIR {
    let mut f = function(name, vec![], None);
    if documented {
        f.docstring = doc("Does something.");
    }
    f
}

fn cls(name: &str, documented: bool, methods: Vec<FunctionIR>) -> ClassIR {
    let mut c = class(name, &[], methods);
    if documented {
        c.docstring = doc("A class.");
    }
    c
}

fn modl(
    name: &str,
    documented: bool,
    classes: Vec<ClassIR>,
    functions: Vec<FunctionIR>,
) -> ModuleIR {
    let mut m = module(name, classes, functions);
    if documented {
        m.docstring = doc("A module.");
    }
    m
}

#[test]
fn percentage_table() {
    let cases = [
        (10, 8, 80.0),
        (0, 0, 100.0),
        (5, 5, 100.0),
        (4, 0, 0.0),
        (3, 2, 2.0 / 3.0 * 100.0),
    ];
    for (total, documented, pct) in cases {
        let result = CoverageResult {
            total,
            documented,
            undocumented: vec![],
        };
        assert_eq!(result.percentage(), pct, "{total}/{documented}");
    }
}

#[test]
fn counting_rules_table() {
    let cases: Vec<(&str, ModuleIR, usize, usize, Vec<&str>)> = vec![
        (
            "documented module",
            modl("mylib.core", true, vec![], vec![]),
            1,
            1,
            vec![],
        ),
        (
            "undocumented module",
            modl("mylib.core", false, vec![], vec![]),
            1,
            0,
            vec!["mylib.core"],
        ),
        (
            "documented function",
            modl("mylib.core", true, vec![], vec![func("greet", true)]),
            2,
            2,
            vec![],
        ),
        (
            "undocumented function",
            modl("mylib.core", true, vec![], vec![func("greet", false)]),
            2,
            1,
            vec!["mylib.core.greet"],
        ),
        (
            "private function skipped",
            modl("mylib.core", true, vec![], vec![func("_helper", false)]),
            1,
            1,
            vec![],
        ),
        (
            "__init__ counts",
            modl(
                "mylib.core",
                true,
                vec![cls("Foo", true, vec![func("__init__", false)])],
                vec![],
            ),
            3,
            2,
            vec!["mylib.core.Foo.__init__"],
        ),
        (
            "documented class",
            modl(
                "mylib.core",
                true,
                vec![cls("Calculator", true, vec![])],
                vec![],
            ),
            2,
            2,
            vec![],
        ),
        (
            "undocumented class",
            modl(
                "mylib.core",
                true,
                vec![cls("Calculator", false, vec![])],
                vec![],
            ),
            2,
            1,
            vec!["mylib.core.Calculator"],
        ),
        (
            "class with methods",
            modl(
                "mylib.core",
                true,
                vec![cls(
                    "Calculator",
                    true,
                    vec![func("add", true), func("subtract", false)],
                )],
                vec![],
            ),
            4,
            3,
            vec!["mylib.core.Calculator.subtract"],
        ),
        (
            "private class skipped",
            modl(
                "mylib.core",
                true,
                vec![cls("_Internal", false, vec![])],
                vec![],
            ),
            1,
            1,
            vec![],
        ),
        (
            "private method skipped",
            modl(
                "mylib.core",
                true,
                vec![cls(
                    "Foo",
                    true,
                    vec![func("public_method", true), func("_private_method", false)],
                )],
                vec![],
            ),
            3,
            3,
            vec![],
        ),
        (
            "whitespace docstring is undocumented",
            {
                let mut m = modl("mylib.core", false, vec![], vec![]);
                m.docstring = doc("   \n ");
                m
            },
            1,
            0,
            vec!["mylib.core"],
        ),
    ];
    for (label, module, total, documented, undocumented) in cases {
        let result = analyze_module(&module);
        assert_eq!(
            (result.total, result.documented),
            (total, documented),
            "{label}"
        );
        assert_eq!(result.undocumented, undocumented, "{label}");
    }
}

#[test]
fn inner_classes_count_recursively_but_types_and_constants_do_not() {
    let mut outer = cls("Outer", true, vec![]);
    outer.inner_classes = vec![cls("Inner", false, vec![func("run", false)])];
    let mut m = modl("mylib.core", true, vec![outer], vec![]);
    m.constants = vec![crate::fixtures::var("MAX", "int", "")];
    m.types = vec![crate::fixtures::type_item(
        "Point",
        folio_ir::TypeKind::Struct,
    )];
    let result = analyze_module(&m);
    assert_eq!(result.total, 4);
    assert_eq!(
        result.undocumented,
        ["mylib.core.Outer.Inner", "mylib.core.Outer.Inner.run"]
    );
}

#[test]
fn full_module_scenario() {
    let m = modl(
        "mylib.api",
        true,
        vec![
            cls(
                "Service",
                true,
                vec![
                    func("__init__", true),
                    func("run", true),
                    func("stop", false),
                    func("_cleanup", false),
                ],
            ),
            cls("_InternalHelper", false, vec![]),
        ],
        vec![
            func("public_func", true),
            func("another_func", false),
            func("_private_func", false),
        ],
    );
    let result = analyze_module(&m);
    assert_eq!((result.total, result.documented), (7, 5));
    let mut undocumented = result.undocumented.clone();
    undocumented.sort();
    assert_eq!(
        undocumented,
        ["mylib.api.Service.stop", "mylib.api.another_func"]
    );
}

#[test]
fn analyze_modules_keeps_order_and_aggregate_sums() {
    let results = analyze_modules(&[
        modl("mylib.core", true, vec![], vec![func("foo", true)]),
        modl("mylib.utils", false, vec![], vec![func("bar", false)]),
    ]);
    assert_eq!(
        results.keys().collect::<Vec<_>>(),
        ["mylib.core", "mylib.utils"]
    );
    assert_eq!(results["mylib.core"].documented, 2);
    assert_eq!(results["mylib.utils"].documented, 0);
    let total = aggregate(&results);
    assert_eq!((total.total, total.documented), (4, 2));
    assert_eq!(total.undocumented, ["mylib.utils", "mylib.utils.bar"]);

    let mut manual = IndexMap::new();
    manual.insert(
        "a".to_string(),
        CoverageResult {
            total: 5,
            documented: 4,
            undocumented: vec!["a.x".to_string()],
        },
    );
    manual.insert(
        "b".to_string(),
        CoverageResult {
            total: 3,
            documented: 2,
            undocumented: vec!["b.y".to_string()],
        },
    );
    let total = aggregate(&manual);
    assert_eq!(
        (total.total, total.documented, total.percentage()),
        (8, 6, 75.0)
    );
    assert_eq!(total.undocumented, ["a.x", "b.y"]);
    let empty = aggregate(&IndexMap::new());
    assert_eq!((empty.total, empty.percentage()), (0, 100.0));
}

#[test]
fn minimum_verdict_and_colour_thresholds() {
    assert_eq!(
        below_minimum(200.0 / 3.0, 80.0).as_deref(),
        Some("Coverage 66.7% is below minimum 80.0%")
    );
    assert_eq!(below_minimum(66.7, 0.0), None);
    assert_eq!(below_minimum(80.0, 80.0), None);
    assert_eq!(
        below_minimum(79.99, 80.0).as_deref(),
        Some("Coverage 80.0% is below minimum 80.0%")
    );
    assert_eq!(coverage_level(80.0), CoverageLevel::High);
    assert_eq!(coverage_level(79.9), CoverageLevel::Medium);
    assert_eq!(coverage_level(50.0), CoverageLevel::Medium);
    assert_eq!(coverage_level(49.9), CoverageLevel::Low);
    assert_eq!(coverage_level(0.0), CoverageLevel::Low);
    assert_eq!(
        NO_MODULES_ERROR,
        "No Python modules found. Check source paths in docs.yaml."
    );
}
