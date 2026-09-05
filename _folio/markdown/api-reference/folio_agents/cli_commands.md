# folio_agents.cli_commands 

The ``folio board`` command group.

Bare ``folio board`` keeps the read-only table view. The write
subcommands (add / move / update / trail / attach) operate on cardfile
boards only — one logical operation, one targeted file edit, optionally
one conventional commit (``--commit``). ``check`` runs the same fail-fast
validation as the build, exposed as a pre-commit/CI gate.

## Functions

### `register` 

```python
def register(app: Any) -> None
```

**Returns:** `None` -
