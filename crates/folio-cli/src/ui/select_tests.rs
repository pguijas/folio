use super::*;

const PRESETS: [Choice; 4] = [
    Choice {
        value: "organic-editorial",
        label: "Organic Editorial",
        description: "Warm editorial docs with rich backgrounds.",
    },
    Choice {
        value: "beacon",
        label: "Beacon",
        description: "Bright product docs with clear contrast.",
    },
    Choice {
        value: "atlas",
        label: "Atlas",
        description: "Structured reference docs with dense navigation.",
    },
    Choice {
        value: "workshop",
        label: "Workshop",
        description: "Practical technical docs with compact rhythm.",
    },
];

fn scripted(keys: Vec<Key>) -> impl FnMut() -> Key {
    let mut keys = keys.into_iter();
    move || keys.next().unwrap_or(Key::Cancel)
}

#[test]
fn prompt_lines_carry_the_exact_escapes() {
    assert_eq!(
            prompt_line("Visual preset"),
            "\x1b[38;5;147m?\x1b[0m \x1b[1mVisual preset\x1b[0m   \x1b[38;5;147m›\x1b[0m \x1b[2m- Use arrow-keys. Return to submit.\x1b[0m"
        );
    assert_eq!(
        completed_line("Docstring style", "auto"),
        "\x1b[32m✔\x1b[0m \x1b[1mDocstring style\x1b[0m \x1b[38;5;147m›\x1b[0m \x1b[1mauto\x1b[0m"
    );
    assert_eq!(
        menu_line("Beacon", true),
        "› \x1b[38;5;147m\x1b[4mBeacon\x1b[0m"
    );
    assert_eq!(menu_line("Beacon", false), "  Beacon");
}

#[test]
fn arrow_selector_moves_down_and_accepts() {
    let mut out = Vec::new();
    let mut keys = scripted(vec![Key::Down, Key::Enter]);
    let result = arrow_choice(
        &mut out,
        &mut keys,
        None,
        "Visual preset",
        &PRESETS,
        "organic-editorial",
    );
    let output = String::from_utf8(out).unwrap();
    assert_eq!(result, Ok("beacon"));
    assert!(output.contains("\x1b[38;5;147m?\x1b[0m \x1b[1mVisual preset\x1b[0m"));
    assert!(output.contains("Use arrow-keys. Return to submit."));
    assert!(output.contains("\x1b[4mOrganic Editorial\x1b[0m"));
    assert!(output.contains("\x1b[4mBeacon\x1b[0m"));
    assert!(output.contains("\x1b[5A"));
    assert!(output.contains("\x1b[2K"));
    assert!(output.contains("✔"));
    assert!(output.ends_with("\x1b[38;5;147m›\x1b[0m \x1b[1mbeacon\x1b[0m\n"));
    // The menu is erased before the completed line: five `up + clear`.
    assert!(output.contains(&"\x1b[1A\x1b[2K".repeat(5)));
}

#[test]
fn arrow_selector_wraps_takes_digits_and_cancels() {
    let mut out = Vec::new();
    let mut keys = scripted(vec![Key::Up, Key::Enter]);
    assert_eq!(
        arrow_choice(
            &mut out,
            &mut keys,
            None,
            "Visual preset",
            &PRESETS,
            "organic-editorial"
        ),
        Ok("workshop")
    );
    let mut keys = scripted(vec![Key::Other, Key::Digit(9), Key::Digit(3)]);
    assert_eq!(
        arrow_choice(
            &mut out,
            &mut keys,
            None,
            "Visual preset",
            &PRESETS,
            "beacon"
        ),
        Ok("atlas")
    );
    let mut out = Vec::new();
    let mut keys = scripted(vec![Key::Down, Key::Cancel]);
    assert_eq!(
        arrow_choice(
            &mut out,
            &mut keys,
            None,
            "Visual preset",
            &PRESETS,
            "beacon"
        ),
        Err(Cancelled::ByUser)
    );
    let output = String::from_utf8(out).unwrap();
    assert!(output.ends_with(&"\x1b[1A\x1b[2K".repeat(5)));
    assert!(!output.contains('✔'));
}

#[test]
fn ticker_state_tracks_rows_below_the_news_line() {
    let mut state = TickerState {
        width: 80,
        rows_below_news: 11,
        active_prompt_lines: 0,
        last_line: String::new(),
        colors: Colors::Off,
    };
    state.add_static_lines(1);
    state.set_active_prompt_lines(5);
    assert_eq!(state.rows_below_news, 17);
    state.set_active_prompt_lines(0);
    state.add_static_lines(1);
    assert_eq!(state.rows_below_news, 13);
    assert_eq!(state.active_prompt_lines, 0);
}

#[test]
fn ticker_thread_stops_promptly() {
    let started = std::time::Instant::now();
    let mut ticker = NewsTicker::start(80, 11, "x", Colors::Off);
    ticker.lock().add_static_lines(1);
    ticker.stop();
    assert!(started.elapsed() < Duration::from_secs(1));
    assert_eq!(ticker.lock().rows_below_news, 12);
}

#[test]
fn numbered_fallback_accepts_index_value_default_and_eof() {
    let ui = Ui {
        colors: Colors::Off,
        tty: false,
        width: 80,
    };
    let ask = |input: &str, default: &str| {
        let mut input = io::Cursor::new(input.as_bytes().to_vec());
        let mut read = || read_piped_line(&mut input);
        numbered_choice(&ui, &mut read, "Visual preset", &PRESETS, default, BOLD)
    };
    assert_eq!(ask("2\n", "organic-editorial"), Ok("beacon"));
    assert_eq!(ask("atlas\n", "organic-editorial"), Ok("atlas"));
    assert_eq!(ask("\n", "beacon"), Ok("beacon"));
    assert_eq!(ask("9\nnope\n4\n", "beacon"), Ok("workshop"));
    assert_eq!(ask("", "beacon"), Err(Cancelled::InputClosed));
}

#[test]
fn typed_answers_are_assembled_from_keys() {
    let script = |keys: &[LineKey]| {
        let mut keys = keys.iter().copied();
        let mut out = Vec::new();
        let result = assemble_line(&mut out, &mut |_| keys.next().unwrap_or(LineKey::Cancel));
        (result, String::from_utf8(out).unwrap())
    };
    assert_eq!(
        script(&[LineKey::Char('2'), LineKey::Enter]),
        (Ok("2".to_string()), "2\r\n".to_string())
    );
    let (result, echoed) = script(&[
        LineKey::Char('1'),
        LineKey::Char('x'),
        LineKey::Backspace,
        LineKey::Other,
        LineKey::Enter,
    ]);
    assert_eq!(result, Ok("1".to_string()));
    assert_eq!(echoed, "1x\x08 \x08\r\n");
    let (result, echoed) = script(&[LineKey::Backspace, LineKey::Char('a'), LineKey::Cancel]);
    assert_eq!(result, Err(Cancelled::ByUser));
    assert_eq!(echoed, "a\r\n");
    // The key reader sees the line so far (Ctrl-D only cancels an empty line).
    let mut seen = Vec::new();
    let mut out = Vec::new();
    let mut keys = [LineKey::Char('a'), LineKey::Enter].into_iter();
    let _ = assemble_line(&mut out, &mut |line| {
        seen.push(line.to_string());
        keys.next().unwrap()
    });
    assert_eq!(seen, ["", "a"]);
}

#[test]
fn early_return_is_enter_and_letters_move_only_unmodified() {
    use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
    let key = |code, modifiers| KeyEvent::new(code, modifiers);
    let none = KeyModifiers::NONE;
    let ctrl = KeyModifiers::CONTROL;
    // A Return typed before raw mode is `\n`, which raw mode reads as Ctrl-J.
    assert_eq!(map_key(key(KeyCode::Char('j'), ctrl)), Key::Enter);
    assert_eq!(map_key(key(KeyCode::Enter, none)), Key::Enter);
    assert_eq!(map_key(key(KeyCode::Char('j'), none)), Key::Down);
    assert_eq!(map_key(key(KeyCode::Char('k'), none)), Key::Up);
    assert_eq!(map_key(key(KeyCode::Char('k'), ctrl)), Key::Other);
    assert_eq!(
        map_key(key(KeyCode::Char('j'), KeyModifiers::ALT)),
        Key::Other
    );
    assert_eq!(map_key(key(KeyCode::Up, none)), Key::Up);
    assert_eq!(map_key(key(KeyCode::Down, none)), Key::Down);
    assert_eq!(map_key(key(KeyCode::Char('q'), none)), Key::Cancel);
    assert_eq!(map_key(key(KeyCode::Char('q'), ctrl)), Key::Other);
    assert_eq!(map_key(key(KeyCode::Char('c'), ctrl)), Key::Cancel);
    assert_eq!(map_key(key(KeyCode::Esc, none)), Key::Cancel);
    assert_eq!(map_key(key(KeyCode::Char('3'), none)), Key::Digit(3));

    assert_eq!(
        map_line_key(key(KeyCode::Char('j'), ctrl), false),
        LineKey::Enter
    );
    assert_eq!(
        map_line_key(key(KeyCode::Char('j'), none), false),
        LineKey::Char('j')
    );
    assert_eq!(
        map_line_key(key(KeyCode::Char('d'), ctrl), true),
        LineKey::Cancel
    );
    assert_eq!(
        map_line_key(key(KeyCode::Char('d'), ctrl), false),
        LineKey::Other
    );
    assert_eq!(
        map_line_key(key(KeyCode::Enter, none), false),
        LineKey::Enter
    );
}
