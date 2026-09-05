# folio_agents.milestones 

Resolve board milestones against each project's own release line.

## Functions

### `resolve_roadmap_phases` 

```python
def resolve_roadmap_phases(board: dict[str, Any], *, raw_roadmap: Any) -> None
```

Attach roadmap phase labels to matching cards and warn on drift.

**Returns:** `None` -
