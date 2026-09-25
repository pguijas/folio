# example_crate

Example crate for Folio's Rust documentation support.

## Functions

### `default_greeting`

```rust
pub fn default_greeting() -> Greeting
```

Produce a default greeting.

## Types

### Struct `Greeting`

```rust
pub struct Greeting
```

A greeting message.

| Field | Type | Description |
| --- | --- | --- |
| `name` | `String` | The name to greet. |

### Impl `Greeting`

```rust
impl Greeting
```

#### `new`

```rust
pub fn new(name: &str) -> Self
```

Create a greeting for the given name.

#### `render`

```rust
pub fn render(&self) -> String
```

Render the greeting as a string.
