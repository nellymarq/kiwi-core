# kiwi-core

Shared tools, agents, and memory primitives extracted from [nellymarq/kiwi](https://github.com/nellymarq/kiwi).
Consumed by:

- **nellymarq/kiwi** (CLI)
- **nellymarq/calsanova** (backend)
- **nellymarq/rwql** (autonomy loop)

**Do not edit consumer-local copies of tools/agents — patch here and bump the pin.**

## Install (consumers)

```
poetry add git+https://github.com/nellymarq/kiwi-core.git@v0.1.0
```

## Development

```
git clone https://github.com/nellymarq/kiwi-core.git
cd kiwi-core
poetry install
poetry run pytest
poetry run ruff check src tests
```

For editable install into a consumer during development:

```
cd ~/consumer && poetry add ../kiwi-core
```

## Package layout

```
src/kiwi_core/
├── tools/      # Domain tools (biomarkers, supplements, periodization, ...)
├── agents/     # Pipeline agents (orchestrator, critique, planning, ...)
└── memory/     # Persistent memory primitives (store, profile)
```

## Versioning

- 0.1.x — Kiwi consumer integration
- 0.2.x — Calsanova consumer integration
- 0.3.x — RWQL consumer integration
- 1.0.0 — all 3 consumers stable for ~1 month

## License

Proprietary — Marques Performance Systems, LLC.
