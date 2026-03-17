# persistence/

The persistence package provides pluggable state storage for per-user session data.

## Interface

`PersistenceBackend` is a `typing.Protocol` (structural subtyping). Any class that implements `save`, `load`, `exists`, `delete`, and `list_users` with matching signatures satisfies the protocol — no explicit inheritance required.

## Implementations

| Class | Location | Notes |
|---|---|---|
| `InMemoryBackend` | `in_memory.py` | Thread-safe dict; deep-copies on save and load to prevent aliasing bugs. State is lost on restart — development and testing only. |

## Error handling

`PersistenceError` (from `life_coach_system.exceptions`) is raised by `InMemoryBackend.delete()` when the user does not exist. Add-new backends should raise the same exception type on unrecoverable failures.
