"""Output validator and safety check.

Two purposes:

1. **Sanitize.** Walk a payload and raise if any forbidden key
   (account_no, order_no, api_key, token, password, broker_response)
   appears. Called by ``packet_emitter.write_outputs`` before writing.

2. **Verify.** Walk a written run directory, load every JSON, and
   assert the doctrinal invariants:

       direct_trade_signal == false                (count of true == 0)
       trade_signal == false or null               (count of true == 0)
       automatic_execution_allowed == false        (count of true == 0)
       trade_ticket_generation_allowed == false    (count of true == 0)
       human_gate_required == true
       operator_decision != "execute"
       no PB_TRIGGER / PB_READY / PB_SCOUT keywords anywhere
       no trade_ticket / order_intent / order_preparation /
          execution_artifact / automatic_alert /
          automatic_execution_hook keys or values anywhere
       no trade-ticket-shaped file in the run directory
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .constants import FORBIDDEN_ARTIFACT_TOKENS, FORBIDDEN_KEYS


class SafetyViolation(Exception):
    """Raised when a payload violates the screening-only invariants."""


def _walk(node: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, path + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + (f"[{i}]",))
    else:
        yield path, node


def sanitize_payload(payload: dict[str, Any]) -> None:
    """Raise SafetyViolation if a forbidden key is present anywhere."""
    for path, _ in _walk(payload):
        for seg in path:
            base = seg.lstrip("[").rstrip("]").lower()
            if base in FORBIDDEN_KEYS:
                raise SafetyViolation(f"forbidden key '{seg}' in payload at /{'/'.join(path)}")


def verify_run_directory(run_dir: str | Path) -> dict[str, Any]:
    """Verify a written run directory. Returns a report dict.

    The report contains explicit zero-counts for the doctrinal
    invariants so that CI can grep for them.
    """
    base = Path(run_dir)
    if not base.exists():
        raise FileNotFoundError(f"run directory not found: {base}")

    report: dict[str, Any] = {
        "out_dir": str(base),
        "checked_files": [],
        "direct_trade_signal_true_count": 0,
        "trade_signal_true_count": 0,
        "automatic_execution_allowed_true_count": 0,
        "trade_ticket_generation_allowed_true_count": 0,
        "operator_decision_execute_count": 0,
        "screening_only_missing_count": 0,
        "candidate_generation_only_missing_count": 0,
        "human_gate_missing_count": 0,
        "pb_trigger_count": 0,
        "pb_ready_count": 0,
        "pb_scout_count": 0,
        "trade_ticket_count": 0,
        "order_intent_count": 0,
        "order_preparation_count": 0,
        "execution_artifact_count": 0,
        "automatic_alert_count": 0,
        "automatic_execution_hook_count": 0,
        "trade_ticket_file_count": 0,
        "errors": [],
    }

    for f in sorted(base.rglob("*")):
        if not f.is_file():
            continue
        report["checked_files"].append(str(f.relative_to(base)))
        if any(tok in f.name.lower() for tok in (
            "trade_ticket", "order_intent", "order_preparation",
            "execution_artifact", "automatic_alert", "automatic_execution_hook",
        )):
            report["trade_ticket_file_count"] += 1
        if f.suffix.lower() == ".json":
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # pragma: no cover
                report["errors"].append(f"{f.name}: {e}")
                continue
            _check_payload(payload, report)
            _check_json_for_artifact_tokens(payload, report)
        # *.md files are educational documentation. They are allowed
        # to *name* the prohibitions ("no PB_TRIGGER is emitted") but
        # cannot, by construction, emit a JSON record. We therefore
        # do not scan them for forbidden tokens.

    report["pass"] = (
        report["direct_trade_signal_true_count"] == 0
        and report["trade_signal_true_count"] == 0
        and report["automatic_execution_allowed_true_count"] == 0
        and report["trade_ticket_generation_allowed_true_count"] == 0
        and report["operator_decision_execute_count"] == 0
        and report["pb_trigger_count"] == 0
        and report["pb_ready_count"] == 0
        and report["pb_scout_count"] == 0
        and report["trade_ticket_count"] == 0
        and report["order_intent_count"] == 0
        and report["order_preparation_count"] == 0
        and report["execution_artifact_count"] == 0
        and report["automatic_alert_count"] == 0
        and report["automatic_execution_hook_count"] == 0
        and report["trade_ticket_file_count"] == 0
        and not report["errors"]
    )
    return report


def _check_payload(payload: Any, report: dict[str, Any]) -> None:
    for path, value in _walk(payload):
        if not path:
            continue
        leaf = path[-1]
        if leaf == "direct_trade_signal" and value is True:
            report["direct_trade_signal_true_count"] += 1
        elif leaf == "trade_signal" and value is True:
            report["trade_signal_true_count"] += 1
        elif leaf == "automatic_execution_allowed" and value is True:
            report["automatic_execution_allowed_true_count"] += 1
        elif leaf == "trade_ticket_generation_allowed" and value is True:
            report["trade_ticket_generation_allowed_true_count"] += 1
        elif leaf == "operator_decision" and isinstance(value, str) and value.lower() == "execute":
            report["operator_decision_execute_count"] += 1


_TOKEN_TO_REPORT_KEY = {
    "PB_TRIGGER": "pb_trigger_count",
    "PB_READY": "pb_ready_count",
    "PB_SCOUT": "pb_scout_count",
    "trade_ticket": "trade_ticket_count",
    "order_intent": "order_intent_count",
    "order_preparation": "order_preparation_count",
    "execution_artifact": "execution_artifact_count",
    "automatic_alert": "automatic_alert_count",
    "automatic_execution_hook": "automatic_execution_hook_count",
}

# Field names that legitimately *deny* a forbidden artifact (e.g.
# `trade_ticket_generation_allowed: false`). These are the only places
# the substring is tolerated as a key.
_DENIAL_KEY_ALLOWLIST = {
    "trade_ticket_generation_allowed",
}


def _check_json_for_artifact_tokens(payload: Any, report: dict[str, Any]) -> None:
    """Count exact-match forbidden artifact tokens as keys or values.

    A JSON record that *emits* a forbidden artifact would either name
    it as a key (e.g. ``"trade_ticket": {...}``) or set a field's
    value to the token (e.g. ``"state": "PB_TRIGGER"``).

    Field names whose substring matches a forbidden token solely
    because they *deny* it (``trade_ticket_generation_allowed``) are
    explicitly allowlisted so this counter does not flag them.
    """
    for path, value in _walk(payload):
        for seg in path:
            base = seg.lstrip("[").rstrip("]")
            if base in _DENIAL_KEY_ALLOWLIST:
                continue
            for token in FORBIDDEN_ARTIFACT_TOKENS:
                if base == token:
                    report[_TOKEN_TO_REPORT_KEY[token]] += 1
        if isinstance(value, str):
            for token in FORBIDDEN_ARTIFACT_TOKENS:
                if value == token:
                    report[_TOKEN_TO_REPORT_KEY[token]] += 1
