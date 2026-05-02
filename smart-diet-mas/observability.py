"""
LLMOps Observability & Logging Module

Provides structured logging for agent inputs/outputs, tool usage,
and execution tracing throughout the multi-agent workflow.
"""
from __future__ import annotations
import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import LOGS_DIR, LOG_FORMAT, LOG_ROTATION, LOG_RETENTION

# Remove default logger
logger.remove()

# Console output (colored, concise)
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# File output (detailed, rotating)
logger.add(
    LOGS_DIR / "mas_system_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    level="DEBUG",
    encoding="utf-8",
)

# Agent-specific trace log
logger.add(
    LOGS_DIR / "agent_trace.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
    level="TRACE",
    filter=lambda record: record["extra"].get("trace", False),
    encoding="utf-8",
)


class AgentTracer:
    """Traces agent execution for observability."""

    def __init__(self) -> None:
        self._traces: list[dict] = []
        self._start_time = datetime.now()

    def log_agent_start(self, agent_name: str, input_data: dict) -> None:
        """Log when an agent starts execution."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "AGENT_START",
            "agent": agent_name,
            "input_summary": self._summarize(input_data),
        }
        self._traces.append(entry)
        logger.info(f"▶ AGENT START: {agent_name}")
        logger.bind(trace=True).trace(json.dumps(entry, default=str))

    def log_agent_end(self, agent_name: str, output_data: dict) -> None:
        """Log when an agent completes execution."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "AGENT_END",
            "agent": agent_name,
            "output_summary": self._summarize(output_data),
        }
        self._traces.append(entry)
        logger.info(f"✔ AGENT END: {agent_name}")
        logger.bind(trace=True).trace(json.dumps(entry, default=str))

    def log_tool_usage(self, tool_name: str, inputs: dict, output: any) -> None:
        """Log tool invocation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "TOOL_CALL",
            "tool": tool_name,
            "inputs": self._summarize(inputs),
            "output_summary": self._summarize(output) if isinstance(output, dict) else str(output)[:200],
        }
        self._traces.append(entry)
        logger.info(f"🔧 TOOL: {tool_name}")
        logger.bind(trace=True).trace(json.dumps(entry, default=str))

    def log_llm_call(self, agent_name: str, prompt_preview: str, response_preview: str) -> None:
        """Log LLM invocation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "LLM_CALL",
            "agent": agent_name,
            "prompt_preview": prompt_preview[:300],
            "response_preview": response_preview[:300],
        }
        self._traces.append(entry)
        logger.debug(f"🤖 LLM call by {agent_name}")
        logger.bind(trace=True).trace(json.dumps(entry, default=str))

    def log_error(self, agent_name: str, error: str) -> None:
        """Log an error."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "ERROR",
            "agent": agent_name,
            "error": error,
        }
        self._traces.append(entry)
        logger.error(f"✗ ERROR in {agent_name}: {error}")

    def get_execution_trace(self) -> list[dict]:
        """Return the full execution trace."""
        return self._traces

    def get_summary(self) -> str:
        """Return a human-readable execution summary."""
        duration = (datetime.now() - self._start_time).total_seconds()
        agent_events = [t for t in self._traces if t["event"] == "AGENT_START"]
        tool_events = [t for t in self._traces if t["event"] == "TOOL_CALL"]
        error_events = [t for t in self._traces if t["event"] == "ERROR"]
        lines = [
            "═" * 50,
            "  EXECUTION TRACE SUMMARY",
            "═" * 50,
            f"  Total Duration: {duration:.2f}s",
            f"  Agents Run:     {len(agent_events)}",
            f"  Tool Calls:     {len(tool_events)}",
            f"  Errors:         {len(error_events)}",
            "─" * 50,
        ]
        for t in self._traces:
            icon = {"AGENT_START": "▶", "AGENT_END": "✔", "TOOL_CALL": "🔧",
                    "LLM_CALL": "🤖", "ERROR": "✗"}.get(t["event"], "•")
            lines.append(f"  {icon} [{t['timestamp'][11:19]}] {t['event']}: {t.get('agent', t.get('tool', ''))}")
        lines.append("═" * 50)
        return "\n".join(lines)

    @staticmethod
    def _summarize(data: any) -> str:
        if isinstance(data, dict):
            return json.dumps({k: str(v)[:80] for k, v in list(data.items())[:10]}, default=str)
        return str(data)[:200]

# Global tracer instance
tracer = AgentTracer()
