# Demo SDLC Agent

A WSO2 Agent Manager-ready demo agent that performs mocked Software Development Lifecycle analysis.

This project exposes two API endpoints:

1. `POST /chat` — an interactive chat endpoint where users can talk to the SDLC agent.
2. `POST /trigger` — a non-interactive trigger endpoint that performs a mocked SDLC analysis and returns a final answer immediately.

The agent is implemented in Python with FastAPI, LangGraph, LangChain, and OpenAI-compatible chat models. It is designed to be used in demos where the agent performs engineering lifecycle tasks such as release-readiness review, pull request review, CI/CD health checks, security/dependency scanning, and test coverage analysis.

The implementation is based on the same structure used by the WSO2 Agent Manager sample agent pattern: a `main.py` entrypoint, FastAPI HTTP endpoints, a LangGraph ReAct-style agent, tools, mocked domain data, and optional OpenTelemetry tracing.

---

## What this agent does

The **SDLC Copilot Agent** acts like a principal software engineering assistant focused on software delivery workflows.

It can answer questions and perform demo analysis related to:

- Release readiness
- Pull request review
- CI/CD health
- Build and deployment risk
- Test coverage gaps
- Security and dependency risk
- Maintainability and complexity findings
- Operational readiness
- Recommended next engineering actions

The agent uses deterministic mocked data. It does **not** connect to a real GitHub repository, Jira project, CI/CD system, SonarQube instance, Snyk instance, Kubernetes cluster, or monitoring platform.

This makes the demo predictable and safe while still showing how an AI agent can call tools, reason over software lifecycle data, and produce an engineering decision.

---

## Demo repositories supported by the mocked data

The agent currently supports two mocked repositories:

### `checkout-service`

A mocked FastAPI payments service.

Example identifiers that map to this repository:

```text
checkout-service
checkout
payments
payment
https://github.com/acme-payments/checkout-service
```

### `inventory-service`

A mocked Spring Boot inventory service.

Example identifiers that map to this repository:

```text
inventory-service
inventory
stock
https://github.com/acme-retail/inventory-service
```

If an unknown repository is provided, the implementation falls back to the default mocked repository:

```text
checkout-service
```

---

## API overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Check whether the service is alive and view basic runtime configuration |
| `POST` | `/chat` | Interactive WSO2 Agent Manager-compatible chat endpoint |
| `POST` | `/trigger` | One-shot non-interactive SDLC analysis endpoint |

---

## Project structure

```text
sdlc-agent/
├── agent.py
├── main.py
├── pytest.ini
├── requirements.txt
├── sdlc_data.py
├── system_prompt.py
├── tools.py
├── tracing.py
└── tests/
    ├── test_agent.py
    └── test_tools.py
```

### File responsibilities

#### `main.py`

Application entrypoint.

This is the file that should be used as the start command in WSO2 Agent Manager:

```bash
python main.py
```

It imports tracing first, then imports the FastAPI app from `agent.py`, and starts Uvicorn.

#### `agent.py`

Main FastAPI application.

It defines:

- `GET /health`
- `POST /chat`
- `POST /trigger`

It also contains:

- LangGraph agent initialization
- OpenAI / WSO2 governed gateway configuration
- In-memory session history
- request/response models
- deterministic formatting for the non-LLM trigger mode

#### `tools.py`

Contains the deterministic mocked SDLC tools used by the agent.

The tools include:

- `get_repository_snapshot`
- `run_static_quality_scan`
- `run_security_dependency_scan`
- `get_ci_cd_health`
- `run_mocked_sdlc_analysis`

These tools are wrapped as LangChain tools and made available to the LangGraph ReAct agent.

#### `sdlc_data.py`

Contains all mocked repository data, findings, metrics, policies, and default values.

This is the source of truth for the demo data.

#### `system_prompt.py`

Contains the agent system prompt.

The default prompt tells the agent how to behave, when to call tools, how to format responses, and how to avoid pretending that it accessed real systems.

#### `tracing.py`

Optional OpenTelemetry / Traceloop initialization.

This is safe by default. If the required tracing environment variables are not present, tracing is skipped.

#### `tests/`

Pytest test suite covering:

- mocked tool behavior
- repository mapping
- trigger endpoint deterministic mode
- health endpoint import safety
- OpenAI configuration resolution

---

## Requirements

- Python 3.11+
- `pip`
- Optional: OpenAI API key or WSO2 Agent Manager governed OpenAI gateway configuration

---

## Local setup

Clone the repository:

```bash
git clone https://github.com/joaokuntzwso2/demo-sdlc-agent.git
cd demo-sdlc-agent
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest tests/ -v
```

---

## Running locally

### Option 1: Run with BYO OpenAI key

Use this when running locally with your own OpenAI-compatible key.

```bash
export OPENAI_API_KEY_DEFAULT="your-openai-api-key"
export OPENAI_MODEL="gpt-4o"
python main.py
```

The service starts on port `8000` by default.

You should see a startup log containing `READY`.

### Option 2: Run with WSO2 Agent Manager governed LLM configuration

Use this when the LLM is accessed through a governed OpenAI-compatible gateway.

```bash
export OPENAI_URL="https://your-governed-openai-compatible-endpoint/v1"
export OPENAI_API_KEY="your-governed-api-key"
export OPENAI_MODEL="gpt-4o"
python main.py
```

In this mode, the implementation sends:

```text
API-Key: <OPENAI_API_KEY>
Authorization:
```

The OpenAI SDK API key value is set to a placeholder internally because the gateway is expected to authenticate using the `API-Key` header.

### Option 3: Run deterministic trigger mode without an LLM key

The `/trigger` endpoint supports `use_llm: false`.

This allows you to test the non-interactive mocked analysis without any OpenAI key.

```bash
python main.py
```

Then call `/trigger` with:

```json
"use_llm": false
```

The `/chat` endpoint still requires a working LLM configuration.

---

## Environment variables

| Variable | Required | Description |
|---|---:|---|
| `PORT` | No | HTTP port. Defaults to `8000`. |
| `OPENAI_MODEL` | No | Chat model name. Defaults to `gpt-4o`. |
| `OPENAI_API_KEY_DEFAULT` | Required for local BYO LLM mode | API key used when `OPENAI_URL` is not set. |
| `OPENAI_URL` | Required for governed mode | OpenAI-compatible gateway base URL. |
| `OPENAI_API_KEY` | Required for governed mode | API key sent to the gateway using the `API-Key` header. |
| `SYSTEM_PROMPT_VARIANT` | No | Prompt variant. Defaults to `baseline`. |
| `AMP_OTEL_ENDPOINT` | No | Enables optional tracing when present with `AMP_AGENT_API_KEY`. |
| `AMP_AGENT_API_KEY` | No | API key for optional tracing. |
| `AMP_AGENT_NAME` | No | Service name used for tracing. Defaults to `sdlc-copilot-agent`. |
| `AMP_AGENT_VERSION` | No | Optional version metadata for tracing. |
| `AMP_TRACE_CONTENT` | No | Controls trace content capture. Defaults to `true`. |

---

## Endpoint details

---

# `GET /health`

Returns basic service readiness information.

## Request

```bash
curl -s http://localhost:8000/health | jq
```

## Example response

```json
{
  "ok": true,
  "name": "sdlc-copilot-agent",
  "model": "gpt-4o",
  "governed": false,
  "port": 8000,
  "endpoints": {
    "chat": "POST /chat",
    "trigger": "POST /trigger",
    "health": "GET /health"
  }
}
```

---

# `POST /chat`

Interactive chat endpoint.

This endpoint is compatible with the common WSO2 Agent Manager chat contract.

## Request body

```json
{
  "message": "Run a release readiness review for checkout-service",
  "session_id": "demo-1",
  "context": {}
}
```

## Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `message` | string | Yes | User message to send to the agent |
| `session_id` | string | Yes | Conversation/session ID used to preserve chat history |
| `context` | object | No | Optional platform context payload |

The service stores recent chat messages in memory using `session_id`.

For demo purposes, this is enough. For production or multi-replica deployments, session state should be moved to a shared store such as Redis or a platform-provided state service.

---

## Chat curl examples

### 1. Release readiness review

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Run a release readiness review for checkout-service.",
    "session_id": "demo-chat-1",
    "context": {}
  }' | jq
```

Expected behavior:

- The agent calls the mocked SDLC analysis tool.
- It returns a decision such as `CONDITIONAL`.
- It explains the highest-risk findings.
- It recommends next engineering actions.

---

### 2. Pull request review

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Review this PR for checkout-service. The change adds retry logic around payment-provider timeouts and modifies receipt-worker queue visibility timeout.",
    "session_id": "demo-chat-2",
    "context": {
      "source": "demo",
      "workflow": "pull_request_review"
    }
  }' | jq
```

Expected behavior:

- The agent treats the request as an SDLC review.
- It uses mocked repository and quality findings.
- It identifies test gaps and reliability risks.
- It provides recommended next actions before approval.

---

### 3. Security review

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Check the security and dependency risk for checkout-service.",
    "session_id": "demo-chat-3",
    "context": {}
  }' | jq
```

Expected behavior:

- The agent calls the mocked security/dependency scan tool.
- It reports vulnerability counts, stale dependencies, and security findings.
- It gives a release gate recommendation.

---

### 4. CI/CD health review

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What is the CI/CD health for inventory-service? Include flaky tests and deployment risk.",
    "session_id": "demo-chat-4",
    "context": {}
  }' | jq
```

Expected behavior:

- The agent calls the mocked CI/CD health tool.
- It reports build status, flaky tests, deployment failures, and risk notes.

---

### 5. Repository snapshot

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Give me a repository snapshot for inventory-service.",
    "session_id": "demo-chat-5",
    "context": {}
  }' | jq
```

Expected behavior:

- The agent returns mocked repository metadata.
- It includes owner team, runtime, framework, deployment target, services, and critical paths.

---

### 6. Continue the same chat session

Because `/chat` stores history by `session_id`, follow-up questions work when the same `session_id` is reused.

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What should we fix first before approving it?",
    "session_id": "demo-chat-1",
    "context": {}
  }' | jq
```

Expected behavior:

- The agent uses prior conversation context from `demo-chat-1`.
- It recommends the highest-priority action from the previous analysis.

---

# `POST /trigger`

Non-interactive one-shot endpoint.

This endpoint is useful for demos where an external event triggers an agent analysis, for example:

- a pull request is opened
- a release candidate is created
- a deployment is requested
- a nightly SDLC audit runs
- a security gate needs an automated summary

Unlike `/chat`, this endpoint does not require user interaction. It accepts an analysis request and returns one final result.

---

## Request body

```json
{
  "repository_url": "https://github.com/acme-payments/checkout-service",
  "branch": "main",
  "analysis_type": "release_readiness",
  "change_summary": "Payment retry logic and receipt-worker queue timeout changes.",
  "use_llm": true
}
```

## Fields

| Field | Type | Required | Default | Description |
|---|---|---:|---|---|
| `repository_url` | string | No | `https://github.com/acme-payments/checkout-service` | Repository URL or mocked repository name |
| `branch` | string | No | `main` | Branch to analyze |
| `analysis_type` | string | No | `release_readiness` | Supported values: `release_readiness`, `pr_review`, `security_scan` |
| `change_summary` | string | No | Demo release-readiness summary | Optional description of the change |
| `use_llm` | boolean | No | `true` | If `true`, uses the LangGraph agent. If `false`, returns deterministic formatted analysis without an LLM call |

---

## Trigger curl examples

### 1. Release-readiness trigger with LLM

```bash
curl -s -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "https://github.com/acme-payments/checkout-service",
    "branch": "main",
    "analysis_type": "release_readiness",
    "change_summary": "Payment retry logic and receipt-worker queue timeout changes.",
    "use_llm": true
  }' | jq
```

Expected behavior:

- The endpoint generates a one-shot analysis request.
- The LangGraph agent calls `run_mocked_sdlc_analysis`.
- The final response includes:
  - decision
  - confidence
  - key findings
  - CI/CD signal
  - security signal
  - recommended next actions

---

### 2. Release-readiness trigger without LLM

This is the easiest endpoint to test when no OpenAI credentials are configured.

```bash
curl -s -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "checkout-service",
    "branch": "main",
    "analysis_type": "release_readiness",
    "change_summary": "Testing deterministic trigger path.",
    "use_llm": false
  }' | jq
```

Expected behavior:

- The endpoint does not call the LLM.
- It returns deterministic mocked analysis from local data.
- This works without `OPENAI_API_KEY_DEFAULT`, `OPENAI_URL`, or `OPENAI_API_KEY`.

---

### 3. Pull-request review trigger

```bash
curl -s -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "checkout-service",
    "branch": "feature/payment-provider-retry",
    "analysis_type": "pr_review",
    "change_summary": "This PR adds retry logic for payment-provider timeout errors and updates receipt-worker queue visibility timeout from 30s to 90s.",
    "use_llm": true
  }' | jq
```

Expected behavior:

- The response focuses on PR review concerns.
- It highlights test gaps, reliability impact, security/dependency risk, and delivery confidence.

---

### 4. Security scan trigger

```bash
curl -s -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "checkout-service",
    "branch": "main",
    "analysis_type": "security_scan",
    "change_summary": "Nightly security gate for the checkout service.",
    "use_llm": true
  }' | jq
```

Expected behavior:

- The response focuses on security and dependency risk.
- It mentions stale dependencies, vulnerability severity, and whether the release should be gated.

---

### 5. Inventory service trigger

```bash
curl -s -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "inventory-service",
    "branch": "main",
    "analysis_type": "release_readiness",
    "change_summary": "Warehouse sync and stock reconciliation changes.",
    "use_llm": false
  }' | jq
```

Expected behavior:

- The response uses the mocked `inventory-service` data.
- It reports integration coverage concerns, dependency risk, CI/CD risk, and recommended remediation.

---

## Example deterministic `/trigger` response

The exact text may vary slightly if `use_llm` is `true`.

With `use_llm: false`, the response follows a deterministic structure similar to:

```json
{
  "analysis_id": "mock-abc1234567",
  "analysis_type": "release_readiness",
  "response": "Decision: CONDITIONAL with medium confidence.\n\nMocked SDLC analysis..."
}
```

The response body includes:

```text
Decision: CONDITIONAL with medium confidence.

Mocked SDLC analysis `mock-...` for `checkout-service` on branch `main`.

Summary:
checkout-service is conditional for release_readiness...

Key findings:
- HIGH: Payment retry path is not covered by integration tests...
- MEDIUM: Payment orchestration function exceeds complexity threshold...
- MEDIUM: JWT dependency is behind the approved baseline...

CI/CD signal:
- Last build: passed
- Flaky tests in last 7 days: 2
- Failed deployments in last 30 days: 1

Security signal:
- Risk: high
- Critical vulnerabilities: 0
- High vulnerabilities: 1
- Secret leaks: 0

Recommended next actions:
- Add provider-timeout and idempotency integration tests before production rollout.
- Split authorization, capture, and rollback decisions into separate units.
- Upgrade to the organization-approved PyJWT baseline and run auth regression tests.
```

---

## Agent tools

The LangGraph agent can call the following mocked tools.

---

### `get_repository_snapshot`

Returns mocked repository metadata.

Useful for:

- repository overview
- owner/team lookup
- runtime/framework lookup
- service/component overview
- critical path overview

Returns data such as:

- repository name
- repository URL
- branch
- domain
- owner team
- runtime
- framework
- deployment target
- service list
- critical paths
- recent changes
- quality metrics
- pipeline metrics
- security metrics
- operational metrics

---

### `run_static_quality_scan`

Returns mocked quality and maintainability findings.

Useful for:

- code quality review
- test gap analysis
- complexity review
- release blockers
- PR review findings

Example finding categories:

- reliability
- maintainability
- security
- delivery
- quality

---

### `run_security_dependency_scan`

Returns mocked dependency and security information.

Useful for:

- vulnerability review
- dependency risk
- stale dependency analysis
- secret leak checks
- release security gate decision

---

### `get_ci_cd_health`

Returns mocked delivery pipeline information.

Useful for:

- build status
- deployment reliability
- flaky tests
- failed deployments
- mean time to restore
- release confidence

---

### `run_mocked_sdlc_analysis`

Runs the full mocked analysis used by `/trigger`.

This combines:

- repository snapshot
- static quality scan
- security/dependency scan
- CI/CD health
- release policy
- decision logic
- recommended actions

This is the primary tool for one-shot analysis.

---

## Analysis decisions

The agent uses the following high-level decision language.

| Decision | Meaning |
|---|---|
| `ready` | The mocked repository has no major blocking signals and is considered safe to proceed |
| `conditional` | The mocked repository can proceed only after specific mitigations or approvals |
| `blocked` | The mocked repository should not proceed until blocking risks are fixed |

The decision is based on mocked signals such as:

- critical vulnerabilities
- high-severity findings
- CI status
- flaky test count
- failed deployment history
- security risk
- test coverage
- operational health

---

## Prompt variants

The agent supports a prompt variant environment variable:

```bash
export SYSTEM_PROMPT_VARIANT=baseline
```

Supported values:

| Value | Description |
|---|---|
| `baseline` | Full SDLC-focused system prompt. Default and recommended. |
| `broken` | Minimal intentionally weak prompt useful for demo comparisons. |

In normal usage, leave this unset or set it to:

```bash
baseline
```

---

## Running tests

```bash
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/test_tools.py -v
```

Run one test:

```bash
pytest tests/test_agent.py::test_trigger_deterministic_endpoint_without_llm -v
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'tools'`

Make sure `pytest.ini` exists at the project root:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Then rerun:

```bash
pytest tests/ -v
```

You can also run:

```bash
PYTHONPATH=. pytest tests/ -v
```

---

### `401`, `403`, or authentication errors from the LLM provider

Check which mode you are using.

For local BYO mode:

```bash
export OPENAI_API_KEY_DEFAULT="your-openai-api-key"
unset OPENAI_URL
unset OPENAI_API_KEY
```

For governed gateway mode:

```bash
export OPENAI_URL="https://your-governed-openai-compatible-endpoint/v1"
export OPENAI_API_KEY="your-governed-api-key"
```

---

### `/trigger` works with `use_llm: false`, but `/chat` fails

This usually means the FastAPI application is working, but the LLM configuration is missing or invalid.

The `/chat` endpoint always uses the LangGraph agent and therefore requires working LLM configuration.

The `/trigger` endpoint can bypass the LLM only when this field is sent:

```json
"use_llm": false
```

---

### Port already in use

Use a different port:

```bash
export PORT=8080
python main.py
```

Then call:

```bash
curl -s http://localhost:8080/health | jq
```

---

### Virtual environment prompt shows `(.venv)`

That means the virtual environment is active.

To exit it:

```bash
deactivate
```

To activate it again:

```bash
source .venv/bin/activate
```

---

## WSO2 Agent Manager deployment notes

For a WSO2 Agent Manager demo, configure the service with:

```text
Start command: python main.py
Port: 8000
Health endpoint: GET /health
Chat endpoint: POST /chat
```

The `/chat` endpoint accepts:

```json
{
  "message": "Run a release readiness review for checkout-service.",
  "session_id": "demo-1",
  "context": {}
}
```

The response shape is:

```json
{
  "response": "..."
}
```

The `/trigger` endpoint is not required for the normal chat contract, but it is useful for demoing event-driven or workflow-driven agent execution.

For example, an external system can call:

```bash
curl -s -X POST https://your-agent-host/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "repository_url": "checkout-service",
    "branch": "main",
    "analysis_type": "release_readiness",
    "change_summary": "Release candidate created from main.",
    "use_llm": true
  }'
```

---

## Important demo limitation

This is a mocked SDLC agent.

It intentionally does not perform real repository scanning, real dependency scanning, real test execution, real CI/CD inspection, or real deployment analysis.

The mocked tools are designed to simulate those systems for a stable demo.

To turn this into a production-grade SDLC agent, replace the mocked tools in `tools.py` and data in `sdlc_data.py` with real integrations, such as:

- GitHub API
- GitLab API
- Azure DevOps API
- Jira API
- SonarQube API
- Snyk API
- Trivy or Grype reports
- CI/CD platform APIs
- Kubernetes APIs
- OpenTelemetry metrics
- Incident management systems
- Internal service catalog