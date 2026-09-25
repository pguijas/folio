use super::*;
use clap::CommandFactory;

#[test]
fn the_tree_is_consistent_and_lists_commands_in_the_guides_order() {
    Cli::command().debug_assert();
    let command = Cli::command();
    let visible: Vec<&str> = command
        .get_subcommands()
        .filter(|c| !c.is_hide_set())
        .map(|c| c.get_name())
        .collect();
    assert_eq!(
        visible,
        ["init", "build", "serve", "coverage", "clean", "roadmap"]
    );
    let hidden: Vec<&str> = command
        .get_subcommands()
        .filter(|c| c.is_hide_set())
        .map(|c| c.get_name())
        .collect();
    assert_eq!(hidden, ["build-versions", "github-pages"]);
    assert!(command.find_subcommand("board").is_none());
    let root: Vec<&str> = command
        .get_arguments()
        .filter(|a| a.get_long().is_some() && a.get_long() != Some("help"))
        .map(|a| a.get_long().unwrap())
        .collect();
    assert_eq!(root, ["version", "update"]);
    let update = Cli::try_parse_from(["folio", "--update"]).unwrap();
    assert!(update.update && update.command.is_none());
    assert!(
        Cli::try_parse_from(["folio", "build", "--update"]).is_err(),
        "--update belongs to the root, not to a command"
    );
}

#[test]
fn build_open_help_mentions_the_blocking_static_preview() {
    let command = Cli::command();
    let build = command.find_subcommand("build").unwrap();
    let open = build
        .get_arguments()
        .find(|a| a.get_long() == Some("open"))
        .unwrap();
    assert_eq!(open.get_short(), Some('o'));
    let help = open.get_help().unwrap().to_string();
    assert!(help.contains("static preview"));
    assert!(help.contains("blocks until interrupted"));
}

#[test]
fn short_flags_and_defaults_match_the_previous_cli() {
    let command = Cli::command();
    let flags = |name: &str| -> Vec<(String, Option<char>)> {
        command
            .find_subcommand(name)
            .unwrap()
            .get_arguments()
            .filter(|a| a.get_long().is_some() && a.get_long() != Some("help"))
            .map(|a| (a.get_long().unwrap().to_string(), a.get_short()))
            .collect()
    };
    assert_eq!(flags("init"), [("yes".to_string(), Some('y'))]);
    assert_eq!(
        flags("serve"),
        [
            ("project-dir".to_string(), None),
            ("verbose".to_string(), Some('v')),
            ("config".to_string(), Some('c')),
            ("port".to_string(), Some('p')),
            ("open".to_string(), Some('o')),
            ("clean".to_string(), None),
            ("previews".to_string(), None),
            ("versions".to_string(), None),
            ("kill-existing".to_string(), None),
        ]
    );
    assert_eq!(
        flags("coverage"),
        [
            ("project-dir".to_string(), None),
            ("config".to_string(), Some('c')),
            ("verbose".to_string(), Some('v')),
            ("min".to_string(), None),
        ]
    );
    assert_eq!(
        flags("clean"),
        [
            ("project-dir".to_string(), None),
            ("config".to_string(), Some('c')),
        ]
    );
    let serve = Cli::try_parse_from(["folio", "serve", "--port", "5678", "x"]).unwrap();
    match serve.command {
        Some(Command::Serve(args)) => {
            assert_eq!(args.port, 5678);
            assert_eq!(args.config, "docs.yaml");
            assert_eq!(args.project.directory, Some(PathBuf::from("x")));
        }
        other => panic!("{other:?}"),
    }
    assert!(Cli::try_parse_from(["folio", "serve", "--port", "abc"]).is_err());
    assert!(Cli::try_parse_from(["folio", "coverage", "--min", "80.5"]).is_ok());
}
