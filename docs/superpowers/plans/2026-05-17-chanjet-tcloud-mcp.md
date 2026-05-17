# Chanjet T+Cloud MCP Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent Python MCP server for Chanjet T+Cloud API documentation lookup, OAuth helpers, and authenticated API calls.

**Architecture:** A small Python package exposes a testable `ChanjetTCloudClient` over a standard-library HTTP transport. MCP integration lives in a thin `server.py` wrapper using `mcp.server.fastmcp.FastMCP`.

**Tech Stack:** Python 3.10+, official `mcp` Python SDK, standard-library `urllib`, standard-library `unittest`.

---

### Task 1: Project Skeleton And Failing Tests

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `tests/test_settings.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing tests**

```python
from chanjet_tcloud_mcp.settings import ChanjetSettings
from chanjet_tcloud_mcp.client import ChanjetTCloudClient
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'chanjet_tcloud_mcp'`.

### Task 2: Settings And Transport

**Files:**
- Create: `src/chanjet_tcloud_mcp/__init__.py`
- Create: `src/chanjet_tcloud_mcp/settings.py`
- Create: `src/chanjet_tcloud_mcp/transport.py`

- [ ] **Step 1: Implement settings and HTTP transport**

`ChanjetSettings.from_env()` reads environment variables and an optional `.env` file. `UrlLibTransport.request()` sends JSON requests and returns parsed JSON.

- [ ] **Step 2: Run tests**

Run: `python3 -m unittest discover -s tests -v`

Expected: client tests still fail because `client.py` is missing; settings tests pass.

### Task 3: Chanjet Client

**Files:**
- Create: `src/chanjet_tcloud_mcp/client.py`

- [ ] **Step 1: Implement `ChanjetTCloudClient`**

Methods:

- `list_tcloud_modules()`
- `get_tcloud_doc(parent_code, module_code)`
- `search_tcloud_docs(query, limit)`
- `call_tplus_api(path, method, body, query, headers)`
- `get_auth_url(redirect_uri, state)`
- `exchange_token(code, redirect_uri)`
- `refresh_token(refresh_token)`

- [ ] **Step 2: Run tests**

Run: `python3 -m unittest discover -s tests -v`

Expected: all unit tests pass.

### Task 4: MCP Server Wrapper

**Files:**
- Create: `src/chanjet_tcloud_mcp/server.py`
- Create: `src/chanjet_tcloud_mcp/__main__.py`

- [ ] **Step 1: Expose MCP tools**

Use `FastMCP("chanjet-tcloud")` and decorate each tool with `@mcp.tool()`.

- [ ] **Step 2: Verify imports without MCP installed**

Run: `python3 -m unittest discover -s tests -v`

Expected: unit tests pass without importing `server.py`.

### Task 5: Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Document setup and MCP client configuration**

Include install, `.env`, run command, and example MCP JSON config.

- [ ] **Step 2: Verify metadata**

Run: `python3 -m py_compile src/chanjet_tcloud_mcp/*.py`

Expected: exit code 0.

### Task 6: Dependency Verification

**Files:**
- Modify: no source changes expected

- [ ] **Step 1: Create virtual environment and install package**

Run: `python3 -m venv .venv && .venv/bin/python -m pip install -e .`

Expected: package and MCP SDK install successfully.

- [ ] **Step 2: Run tests in virtual environment**

Run: `.venv/bin/python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 3: Verify server import**

Run: `.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"`

Expected: prints `chanjet-tcloud`.

