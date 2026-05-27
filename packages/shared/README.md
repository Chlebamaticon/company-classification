# packages/shared

`salespatriot_shared` — contracts and helpers used by every backend service.

| Module        | Status     | Notes                                                                       |
| ------------- | ---------- | --------------------------------------------------------------------------- |
| `messages.py` | done       | Pydantic envelopes. Other agents code against this verbatim.                |
| `fsc.py`      | done       | `FSCCatalog.load()` reader for `data/fsc_catalog.json`.                     |
| `mq.py`       | stub       | Classification Worker agent fills in `connect()` and `RpcClient`.           |
| `db.py`       | stub       | Classification Worker agent fills in `get_engine()` and `emit_event()`.    |
| `llm.py`      | stub       | Classification Worker agent fills in `chat_json()`.                         |

Install in editable mode locally:

```bash
pip install -e packages/shared
pytest packages/shared/tests
```

The Dockerfiles of every backend service should also install this package
(e.g. `pip install ./packages/shared`).
