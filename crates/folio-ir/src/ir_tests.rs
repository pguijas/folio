use super::*;
use serde_json::{json, Value};

fn function(name: &str) -> FunctionIR {
    FunctionIR {
        name: name.to_string(),
        args: vec![],
        returns: None,
        raises: vec![],
        decorators: vec![],
        docstring: DocstringIR::default(),
        is_async: false,
        source_file: "f.py".to_string(),
        line_number: 1,
        kind: FunctionKind::default(),
        signature: String::new(),
        visibility: String::new(),
    }
}

fn keys(value: &Value) -> Vec<&str> {
    value
        .as_object()
        .expect("object")
        .keys()
        .map(String::as_str)
        .collect()
}

#[test]
fn docstring_ir_defaults_and_deserialises_without_the_appended_keys() {
    let doc: DocstringIR =
        serde_json::from_value(json!({"short_description": "Hello."})).expect("defaults fill in");
    assert_eq!(doc.short_description, "Hello.");
    assert_eq!(doc.long_description, "");
    assert!(doc.examples.is_empty());
    assert!(doc.notes.is_empty());
    assert_eq!(DocstringIR::default().short_description, "");
}

#[test]
fn arg_ir_default_keeps_the_string_and_kind_defaults_to_regular() {
    let arg: ArgIR = serde_json::from_value(json!({
        "name": "verbose", "type": "bool", "default": "False", "description": "Verbose mode."
    }))
    .expect("kind defaults");
    assert_eq!(arg.default.as_deref(), Some("False"));
    assert_eq!(arg.kind, ArgKind::Regular);
}

#[test]
fn arg_and_function_kind_ids_round_trip() {
    for (kind, id) in [
        (ArgKind::Regular, "regular"),
        (ArgKind::PositionalOnly, "positional_only"),
        (ArgKind::KeywordOnly, "keyword_only"),
        (ArgKind::VarPositional, "var_positional"),
        (ArgKind::VarKeyword, "var_keyword"),
    ] {
        assert_eq!(serde_json::to_value(kind).unwrap(), json!(id));
        assert_eq!(serde_json::from_value::<ArgKind>(json!(id)).unwrap(), kind);
    }
    for (kind, id) in [
        (FunctionKind::Function, "function"),
        (FunctionKind::Method, "method"),
        (FunctionKind::Property, "property"),
        (FunctionKind::Staticmethod, "staticmethod"),
        (FunctionKind::Classmethod, "classmethod"),
    ] {
        assert_eq!(serde_json::to_value(kind).unwrap(), json!(id));
        assert_eq!(
            serde_json::from_value::<FunctionKind>(json!(id)).unwrap(),
            kind
        );
    }
}

#[test]
fn function_ir_kind_signature_and_visibility_default_and_keep_explicit_values() {
    let pre_seam = json!({
        "name": "f", "args": [], "returns": null, "raises": [], "decorators": [],
        "docstring": {"short_description": ""}, "is_async": false,
        "source_file": "f.py", "line_number": 1
    });
    let func: FunctionIR = serde_json::from_value(pre_seam).expect("appended keys default");
    assert_eq!(func.kind, FunctionKind::Function);
    assert_eq!(func.signature, "");
    assert_eq!(func.visibility, "");

    let raw = FunctionIR {
        signature: "pub fn f()".to_string(),
        visibility: "pub".to_string(),
        ..function("f")
    };
    assert_eq!(raw.signature, "pub fn f()");
    assert_eq!(raw.visibility, "pub");
}

#[test]
fn class_ir_inner_classes_default_and_nest() {
    let cls: ClassIR = serde_json::from_value(json!({
        "name": "C", "bases": [], "decorators": [], "docstring": {"short_description": ""},
        "methods": [], "class_vars": []
    }))
    .expect("inner_classes defaults");
    assert!(cls.inner_classes.is_empty());
    assert_eq!(cls.source_file, "");
    assert_eq!(cls.line_number, 0);

    let outer = ClassIR {
        name: "Outer".to_string(),
        inner_classes: vec![ClassIR {
            name: "Inner".to_string(),
            ..cls.clone()
        }],
        methods: vec![function("add")],
        ..cls
    };
    assert_eq!(outer.inner_classes[0].name, "Inner");
    assert_eq!(outer.methods[0].name, "add");
}

#[test]
fn module_ir_defaults_to_python_without_types() {
    let module: ModuleIR = serde_json::from_value(json!({
        "name": "mylib.core", "docstring": {"short_description": "A test module."},
        "classes": [], "functions": [], "constants": [], "source_file": "mylib/core.py"
    }))
    .expect("language and types default");
    assert_eq!(module.name, "mylib.core");
    assert_eq!(module.source_file, "mylib/core.py");
    assert_eq!(module.language, Language::Python);
    assert!(module.types.is_empty());
}

#[test]
fn language_ids_and_labels() {
    for (lang, id, label) in [
        (Language::Python, "python", "Python"),
        (Language::Javascript, "javascript", "JavaScript"),
        (Language::Rust, "rust", "Rust"),
    ] {
        assert_eq!(lang.id(), id);
        assert_eq!(lang.label(), label);
        assert_eq!(Language::parse(id), Some(lang));
        assert_eq!(serde_json::to_value(lang).unwrap(), json!(id));
    }
    assert_eq!(Language::parse("cobol"), None);
    assert_eq!(Language::default(), Language::Python);
}

#[test]
fn language_fields_are_appended_after_the_python_fields() {
    let module = ModuleIR {
        name: "m".to_string(),
        docstring: DocstringIR::default(),
        classes: vec![],
        functions: vec![function("f")],
        constants: vec![],
        source_file: "m.py".to_string(),
        language: Language::Python,
        types: vec![],
    };
    let value = serde_json::to_value(&module).unwrap();
    assert_eq!(
        keys(&value),
        [
            "name",
            "docstring",
            "classes",
            "functions",
            "constants",
            "source_file",
            "language",
            "types"
        ]
    );
    let function_keys = keys(&value["functions"][0]);
    assert_eq!(
        &function_keys[function_keys.len() - 3..],
        ["kind", "signature", "visibility"]
    );
    assert_eq!(value["functions"][0]["returns"], Value::Null);
    assert_eq!(value["docstring"]["examples"], json!([]));
    assert_eq!(value["functions"][0]["signature"], json!(""));
}

#[test]
fn type_ir_defaults_and_carries_fields_variants_and_methods() {
    let item: TypeIR = serde_json::from_value(json!({
        "name": "Point", "kind": "struct", "docstring": {"short_description": "A point."}
    }))
    .expect("lists default");
    assert!(item.fields.is_empty());
    assert!(item.variants.is_empty());
    assert!(item.methods.is_empty());
    assert!(item.bases.is_empty());
    assert_eq!(item.signature, "");
    assert_eq!(item.visibility, "");
    assert_eq!(item.source_file, "");
    assert_eq!(item.line_number, 0);

    let shape = TypeIR {
        name: "Shape".to_string(),
        kind: TypeKind::Enum,
        fields: vec![VarIR {
            name: "x".to_string(),
            ty: "f64".to_string(),
            value: String::new(),
            description: String::new(),
        }],
        variants: vec![VarIR {
            name: "Circle".to_string(),
            ty: "f64".to_string(),
            value: String::new(),
            description: "Round.".to_string(),
        }],
        methods: vec![FunctionIR {
            kind: FunctionKind::Method,
            signature: "pub fn norm(&self)".to_string(),
            ..function("norm")
        }],
        bases: vec!["Display".to_string()],
        line_number: 7,
        ..item
    };
    assert_eq!(shape.fields[0].name, "x");
    assert_eq!(shape.variants[0].description, "Round.");
    assert_eq!(shape.methods[0].signature, "pub fn norm(&self)");
    assert_eq!(shape.bases, ["Display"]);
    assert_eq!(shape.line_number, 7);
}

#[test]
fn type_kind_accepts_every_documented_kind_and_rejects_others() {
    let all = [
        ("struct", TypeKind::Struct, "Struct"),
        ("enum", TypeKind::Enum, "Enum"),
        ("trait", TypeKind::Trait, "Trait"),
        ("interface", TypeKind::Interface, "Interface"),
        ("type_alias", TypeKind::TypeAlias, "Type"),
        ("union", TypeKind::Union, "Union"),
        ("impl", TypeKind::Impl, "Impl"),
    ];
    for (id, kind, label) in all {
        assert_eq!(TypeKind::parse(id), Ok(kind));
        assert_eq!(kind.label(), label);
        assert_eq!(serde_json::to_value(kind).unwrap(), json!(id));
        assert_eq!(serde_json::from_value::<TypeKind>(json!(id)).unwrap(), kind);
    }
    let expected = "TypeIR.kind must be one of ['enum', 'impl', 'interface', 'struct', 'trait', 'type_alias', 'union'], got 'class'";
    assert_eq!(TypeKind::parse("class").unwrap_err().to_string(), expected);
    let err = serde_json::from_value::<TypeIR>(json!({
        "name": "T", "kind": "class", "docstring": {"short_description": ""}
    }))
    .unwrap_err();
    assert!(err.to_string().starts_with(expected), "{err}");
}

#[test]
fn var_ir_fields() {
    let var: VarIR = serde_json::from_value(json!({
        "name": "MAX_RETRIES", "type": "int", "value": "3", "description": "Max retries."
    }))
    .unwrap();
    assert_eq!(var.name, "MAX_RETRIES");
    assert_eq!(var.ty, "int");
    assert_eq!(serde_json::to_value(&var).unwrap()["type"], json!("int"));
}
