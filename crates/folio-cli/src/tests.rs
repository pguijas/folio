use super::*;

#[test]
fn an_extension_receives_its_arguments_and_preserves_handler_errors() {
    let extensions = [CommandExtension {
        command: Command::new("inspect").arg(clap::Arg::new("path").required(true)),
        run: |matches, output, color| {
            assert!(!color);
            write!(output, "{}", matches.get_one::<String>("path").unwrap())
                .map_err(|error| error.to_string())?;
            Err("extension refused".to_string())
        },
    }];
    let matches = command(&extensions)
        .unwrap()
        .try_get_matches_from(["folio", "inspect", "example"])
        .unwrap();
    let mut output = Vec::new();
    assert_eq!(
        dispatch_extension(&matches, &extensions, &mut output, false),
        Some(Err("extension refused".to_string()))
    );
    assert_eq!(output, b"example");
    assert!(command(&[])
        .unwrap()
        .try_get_matches_from(["folio", "inspect", "example"])
        .is_err());
}

#[test]
fn duplicate_extension_commands_return_an_error() {
    let extension = |name| CommandExtension {
        command: Command::new(name),
        run: |_, _, _| Ok(()),
    };
    for extensions in [
        vec![extension("build")],
        vec![extension("inspect"), extension("inspect")],
    ] {
        let error = command(&extensions).unwrap_err();
        assert_eq!(error.kind(), ErrorKind::ArgumentConflict);
        assert!(error.to_string().contains("Command already registered:"));
    }
}
