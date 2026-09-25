use super::*;

#[test]
fn test_repr_str_basic() {
    assert_eq!(repr_str("abc"), "'abc'");
    assert_eq!(repr_str("it's"), "\"it's\"");
    assert_eq!(repr_str("say \"hi\""), "'say \"hi\"'");
}

#[test]
fn test_repr_int_decimal() {
    assert_eq!(big_int_to_decimal("0xFF"), "255");
    assert_eq!(big_int_to_decimal("0o17"), "15");
    assert_eq!(big_int_to_decimal("0b101"), "5");
    assert_eq!(big_int_to_decimal("1_000"), "1000");
}

#[test]
fn test_repr_float() {
    assert_eq!(repr_float(1000.0), "1000.0");
    assert_eq!(repr_float(0.5), "0.5");
    assert_eq!(repr_float(5.0), "5.0");
}

#[test]
fn test_repr_bytes() {
    assert_eq!(repr_bytes(b"abc"), "b'abc'");
    assert_eq!(repr_bytes(&[0, 255]), "b'\\x00\\xff'");
}

#[test]
fn test_is_printable() {
    assert!(is_printable('a'));
    assert!(is_printable(' '));
    assert!(!is_printable('\0'));
    assert!(!is_printable('\x7f'));
    assert!(!is_printable('\u{00AD}')); // soft hyphen
    assert!(!is_printable('\u{200B}')); // zero width space
    assert!(!is_printable('\u{FEFF}')); // BOM
}
