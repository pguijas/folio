use super::*;

fn parsed(source: &str) -> ModuleIR {
    parse_source(source, "demo", "src/lib.rs").expect("the source parses")
}

#[test]
fn an_inline_module_publishes_on_the_page_of_the_file_that_declares_it() {
    let module = parsed(
        "/// Kept.\npub mod inner {\n    /// Deep.\n    pub fn deep() {}\n    fn hidden() {}\n}\n\nmod secret {\n    pub fn buried() {}\n}\n",
    );
    let names: Vec<&str> = module.functions.iter().map(|f| f.name.as_str()).collect();
    assert_eq!(names, ["deep"]);
    assert_eq!(module.functions[0].line_number, 4);
}

#[test]
fn private_items_and_macros_are_not_documentation() {
    let module = parsed(
        "fn private() {}\nconst SECRET: u8 = 1;\nuse std::fmt;\nmacro_rules! noop {\n    () => {};\n}\nnoop!();\nstruct Hidden;\n",
    );
    assert!(module.functions.is_empty());
    assert!(module.constants.is_empty());
    assert!(module.types.is_empty());
}

#[test]
fn a_signature_reads_on_one_line_whatever_the_wrapping() {
    let module = parsed(
        "/// Wrapped.\n#[inline]\npub fn wrapped(\n    first: u8,\n    second: u8,\n) -> u8 {\n    first\n}\n",
    );
    let wrapped = &module.functions[0];
    assert_eq!(
        wrapped.signature,
        "pub fn wrapped( first: u8, second: u8, ) -> u8"
    );
    assert_eq!(wrapped.decorators, ["#[inline]"]);
    assert_eq!(wrapped.line_number, 3);
}

#[test]
fn only_plain_pub_and_not_doc_hidden_is_public_api() {
    let module = parsed(concat!(
        "pub fn shown() {}\n",
        "pub(crate) fn in_crate() {}\n",
        "pub(super) fn in_parent() {}\n",
        "#[doc(hidden)]\npub fn hidden() {}\n",
        "#[doc(hidden)]\npub struct Hidden;\n",
        "pub struct Shown {\n    pub open: u8,\n    pub(crate) inner: u8,\n    #[doc(hidden)]\n    pub secret: u8,\n}\n",
        "pub enum Mode {\n    On,\n    #[doc(hidden)]\n    __Nonexhaustive,\n}\n",
        "impl Shown {\n    pub fn open(&self) {}\n    pub(crate) fn inner(&self) {}\n    #[doc(hidden)]\n    pub fn secret(&self) {}\n}\n",
    ));
    let functions: Vec<&str> = module.functions.iter().map(|f| f.name.as_str()).collect();
    assert_eq!(functions, ["shown"]);
    let types: Vec<&str> = module.types.iter().map(|t| t.name.as_str()).collect();
    assert_eq!(types, ["Shown", "Mode", "Shown"]);
    let fields: Vec<&str> = module.types[0]
        .fields
        .iter()
        .map(|f| f.name.as_str())
        .collect();
    assert_eq!(fields, ["open"]);
    let variants: Vec<&str> = module.types[1]
        .variants
        .iter()
        .map(|v| v.name.as_str())
        .collect();
    assert_eq!(variants, ["On"]);
    let methods: Vec<&str> = module.types[2]
        .methods
        .iter()
        .map(|m| m.name.as_str())
        .collect();
    assert_eq!(methods, ["open"]);
}

#[test]
fn an_impl_of_a_private_type_or_trait_is_not_public_api() {
    let module = parsed(concat!(
        "struct Private;\n",
        "impl Private {\n    pub fn new() -> Self { Private }\n}\n",
        "trait Sealed {}\n",
        "pub struct Open;\n",
        "impl Sealed for Open {}\n",
        "impl Clone for Private {\n    fn clone(&self) -> Self { Private }\n}\n",
        "impl Clone for Open {\n    fn clone(&self) -> Self { Open }\n}\n",
    ));
    let types: Vec<(&str, Vec<String>)> = module
        .types
        .iter()
        .map(|t| (t.name.as_str(), t.bases.clone()))
        .collect();
    assert_eq!(
        types,
        [("Open", vec![]), ("Open", vec!["Clone".to_string()])]
    );
}
