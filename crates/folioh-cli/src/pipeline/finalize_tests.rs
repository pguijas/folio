use super::*;

#[test]
fn the_timestamp_is_utc_to_the_second_with_a_z() {
    let stamp = build_timestamp();
    assert_eq!(stamp.len(), 20, "{stamp}");
    assert!(stamp.ends_with('Z') && &stamp[10..11] == "T");
    assert!(stamp[..4].chars().all(|c| c.is_ascii_digit()));
}
