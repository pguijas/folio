use super::*;

#[test]
fn near_spellings_find_their_key_and_far_ones_do_not() {
    let keys = ["name", "version", "repo", "repo_ref", "url"];
    assert_eq!(closest_match("vesion", keys), Some("version"));
    assert_eq!(closest_match("repoRef", keys), Some("repo_ref"));
    assert_eq!(closest_match("Name", keys), Some("name"));
    assert_eq!(closest_match("homepage", keys), None);
    assert_eq!(closest_match("urls", keys), Some("url"));
    // Short words allow one edit, not two.
    assert_eq!(closest_match("rpeo", keys), None);
    assert_eq!(closest_match("dark-mode", ["dark_mode"]), Some("dark_mode"));
}

#[test]
fn did_you_mean_is_empty_without_a_near_candidate() {
    assert_eq!(
        did_you_mean("atlass", ["atlas", "beacon"]),
        " (did you mean 'atlas'?)"
    );
    assert_eq!(did_you_mean("zzz", ["atlas", "beacon"]), "");
}
