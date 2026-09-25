# greet

Greeting utilities.

## Constants

| Constant | Type | Value | Description |
| --- | --- | --- | --- |
| `DEFAULT_GREETING` |  | `"Hello!"` | The default greeting. |

## Functions

### `greet`

```javascript
export function greet(name, loud = false)
```

Greet someone by name.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `string` |  | The person to greet. |
| `loud` | `boolean` | `false` | Whether to shout. |

**Returns:** `string` - A greeting message.

```javascript
greet("world")
```
