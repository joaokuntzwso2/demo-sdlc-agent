"""WSO2 Agent Manager entrypoint.

Agent Manager start command:
    python main.py

Local development:
    python main.py
    # or
    python agent.py
"""

from __future__ import annotations
import os
import uvicorn
# Must be imported before `agent` so tracing/instrumentation wraps LangChain early.
import tracing  # noqa: F401
from agent import app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)