
# AGENTS.md: mcp-email-server Coding Standards, Architecture, and Agent Guidance

## 1. Project Overview
mcp-email-server is a modular, test-driven Python MCP server for IMAP/SMTP email. It integrates with MCP clients and Claude Desktop, supporting extensibility, robust error handling, and modern development workflows.

## 2. Directory & Module Structure

```
mcp_email_server/
	app.py         # MCP FastAPI entry, resource/tool definitions
	cli.py         # Typer CLI: stdio, sse, ui, reset
	config.py      # Pydantic config models, settings logic
	log.py         # Loguru-based logging, env config
	ui.py          # Gradio UI for config and status
	emails/
		classic.py   # IMAP/SMTP client, handler logic
		dispatcher.py# Handler dispatch, account routing
		models.py    # Email data models (Pydantic)
		provider/    # Extensible provider logic
	tools/
		installer.py # Desktop config installer
tests/           # Pytest unit tests, fixtures, mocks
docs/            # MkDocs documentation
dev/             # Dev scripts/configs
.github/         # CI/CD workflows, Copilot instructions
```

## 3. Architecture & Data Flow

**Startup:**
1. CLI entry (`cli.py`) or Docker ENTRYPOINT launches MCP server (`app.py`).
2. Loads config (`config.py`), sets up logging (`log.py`).
3. Registers MCP resources/tools (email account, send, page, etc).

**Email Handling:**
1. Dispatcher (`dispatcher.py`) selects handler (classic/provider) per account.
2. Handler (`classic.py`) connects via IMAP/SMTP, fetches/sends emails.
3. Data models (`models.py`) ensure type safety and validation.

**UI & Integration:**
1. Gradio UI (`ui.py`) for config and status.
2. Desktop installer (`tools/installer.py`) for Claude Desktop integration.

**Testing:**
1. Pytest-based tests for all modules, with fixtures and mocks.

## 4. Coding Standards & Best Practices

- PEP8, type hints, and docstrings for all public code.
- Use Pydantic for all config/data models.
- Loguru for logging; configure via `MCP_EMAIL_SERVER_LOG_LEVEL`.
- Typer for CLI; FastMCP for server.
- All MCP tools/resources must be annotated and documented.
- Use fixtures/mocks for all external dependencies in tests.
- All new code must include unit tests and documentation.

## 5. Development Workflow (Checklist)

1. Fork and clone repo.
2. Install environment: `uv sync`
3. Install pre-commit: `uv run pre-commit install`
4. Create feature/fix branch.
5. Write code with type hints, docstrings, and tests.
6. Run `make check` and `make test`.
7. Run `tox` for multi-version tests.
8. Update docs in `docs/` and `README.md`.
9. Commit, push, and open PR.
10. Ensure PR includes tests and docs.

## 6. Build, Deployment, and Integration

- Build wheel: `make build`
- Publish: `make build-and-publish` (PyPI)
- Docker: Build from `Dockerfile`, publish to GHCR (`ghcr.io/hubertusgbecker/mcp-email-server:latest`)
- Use `docker compose` for integration/deployment.
- Desktop integration via `tools/installer.py` and config templates.

## 7. Error Handling & Security

- Validate all inputs with Pydantic.
- Log errors with context using Loguru.
- Never log sensitive data (passwords, tokens).
- Use environment variables for secrets/config.
- All external calls (IMAP/SMTP) must handle exceptions and log failures.

## 8. Testing & Coverage

- All modules require tests in `tests/`.
- Use Pytest fixtures for setup/mocking.
- Run `pytest --cov` for coverage; report via Codecov.
- Test edge cases, error paths, and integration points.

## 9. Documentation

- All public APIs, CLI commands, and MCP tools must be documented in `docs/` and `README.md`.
- Use MkDocs for building/serving docs: `make docs`

## 10. Contribution Guidelines

- Follow steps in `CONTRIBUTING.md`.
- All PRs must include tests and documentation updates.
- Use clear, direct, step-by-step, fact-based style in code and docs.

## 11. Agent Decision-Making & Guidance

- Always refer to AGENTS.md for standards and structure.
- Apply copilot-instructions.md principles: accuracy, clarity, actionable steps, and fact-based reasoning.
- If unsure, state so and request clarification.
- Prefer modular, testable, and documented solutions.
- Summarize key takeaways and next steps in all communications.

## 12. Integration Points & Extensibility

- MCP tools/resources are extensible; add new handlers/providers in `emails/provider/`.
- Desktop integration via config templates and installer.
- Docker and Smithery support for deployment and automation.

## 13. Key Takeaways

- Modular, test-driven, and well-documented codebase.
- Use MCP, Pydantic, Typer, Loguru, uv, Docker, and Gradio as core technologies.
- All changes must be tested, documented, and follow contribution workflow.

---
This document is the true north star for all agents and contributors. Always iterate and improve for clarity, completeness, and actionable guidance. If you see gaps, update this file and communicate improvements.

