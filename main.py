"""WSO2 Agent Manager entrypoint.

Agent Manager start command:
    python main.py

Local development:
    python main.py
    # or
    python agent.py
"""

from __future__ import annotations
import uvicorn
from agent import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)