# folio_agents.worktree 

Read a board branch through an isolated Git worktree.

## Functions

### `sync_board_worktree` 

```python
def sync_board_worktree(project_dir: Path, ref: str) -> Path
```

Return a clean detached worktree at the current board ref.

A local branch wins so a repository with a dedicated board worktree can
preview its latest committed state without pushing. CI normally has no
local board branch, so it fetches the named branch from ``origin`` and
checks out that remote commit instead.

**Returns:** `Path` - 

### `_branch_name` 

```python
def _branch_name(ref: str) -> str
```

**Returns:** `str` - 

### `_resolve_commit` 

```python
def _resolve_commit(repo: Path, branch: str) -> str
```

**Returns:** `str` - 

### `_try_commit` 

```python
def _try_commit(repo: Path, ref: str) -> str
```

**Returns:** `str` - 

### `_worktree_name` 

```python
def _worktree_name(branch: str) -> str
```

**Returns:** `str` - 

### `_git` 

```python
def _git(cwd: Path, *args: str) -> None
```

**Returns:** `None` - 

### `_git_output` 

```python
def _git_output(cwd: Path, *args: str) -> str
```

**Returns:** `str` -
