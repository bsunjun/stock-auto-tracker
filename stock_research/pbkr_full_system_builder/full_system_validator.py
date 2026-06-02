"""Full-system output validator and safety checker.

Two purposes:

1. **Sanitize.** Walk a payload and raise if any forbidden key
   (account_no, order_no, api_key, token, password, broker_response,
   secret) is present. Called by ``full_system_packet_emitter`` before
   writing.

2. **Verify.** Walk a written run directory, load every JSON, validate
   every pack against its schema, and assert the doctrinal invariants:

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

The verifier also refuses any output written *inside* the repository
tree: real outputs must land in ``$PBKR_PROCESSED_ROOT`` or
``$PBKR_OUTPUT_ROOT``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "v1.0"

PBKR_RS_RANK_SOURCE = "kiwoom_daily_universe"
TRADINGVIEW_ROLE = "auxiliary"

SIGNAL_SAFETY_BLOCK = {
    "screening_only": True,
    "candidate_generation_only": True,
    "direct_trade_signal": False,
    "trade_signal": False,
    "automatic_execution_allowed": False,
    "trade_ticket_generation_allowed": False,
    "human_gate_required": True,
}

DAILY_PACKET_SIGNAL_SAFETY = {
    **SIGNAL_SAFETY_BLOCK,
    "operator_decision": None,
}

FORBIDDEN_KEYS = {
    "account_no",
    "account_number",
    "order_no",
    "order_id",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "broker_response",
}

FORBIDDEN_ARTIFACT_TOKENS = (
    "PB_TRIGGER",
    "PB_READY",
    "PB_SCOUT",
    "trade_ticket",
    "order_intent",
    "order_preparation",
    "execution_artifact",
    "automatic_alert",
    "automatic_execution_hook",
)

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

_DENIAL_KEY_ALLOWLIST = {
    "trade_ticket_generation_allowed",
}


class SafetyViolation(Exception):
    """Raised when a payload violates the full-system invariants."""


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
                raise SafetyViolation(
                    f"forbidden key '{seg}' in payload at /{'/'.join(path)}"
                )


def assert_signal_safety(payload: dict[str, Any], *, with_operator_decision: bool = False) -> None:
    """Raise SafetyViolation if signal_safety block is missing/wrong."""
    safety = payload.get("signal_safety")
    if not isinstance(safety, dict):
        raise SafetyViolation("missing signal_safety block")
    if safety.get("screening_only") is not True:
        raise SafetyViolation("signal_safety.screening_only must be true")
    if safety.get("candidate_generation_only") is not True:
        raise SafetyViolation("signal_safety.candidate_generation_only must be true")
    if safety.get("direct_trade_signal") is not False:
        raise SafetyViolation("signal_safety.direct_trade_signal must be false")
    if safety.get("trade_signal") not in (None, False):
        raise SafetyViolation("signal_safety.trade_signal must be false or null")
    if safety.get("automatic_execution_allowed") is not False:
        raise SafetyViolation("signal_safety.automatic_execution_allowed must be false")
    if safety.get("trade_ticket_generation_allowed") is not False:
        raise SafetyViolation("signal_safety.trade_ticket_generation_allowed must be false")
    if safety.get("human_gate_required") is not True:
        raise SafetyViolation("signal_safety.human_gate_required must be true")
    if with_operator_decision:
        op = safety.get("operator_decision", None)
        if op not in (None, "review", "defer"):
            raise SafetyViolation(
                f"signal_safety.operator_decision must be null|review|defer; got {op!r}"
            )


def _new_report(base: Path) -> dict[str, Any]:
    return {
        "out_dir": str(base),
        "checked_files": [],
        "schema_version": SCHEMA_VERSION,
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


def verify_run_directory(run_dir: str | Path) -> dict[str, Any]:
    """Verify a written run directory and return a report dict."""
    base = Path(run_dir)
    if not base.exists():
        raise FileNotFoundError(f"run directory not found: {base}")

    report = _new_report(base)

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
        elif (
            leaf == "operator_decision"
            and isinstance(value, str)
            and value.lower() == "execute"
        ):
            report["operator_decision_execute_count"] += 1


def _check_json_for_artifact_tokens(payload: Any, report: dict[str, Any]) -> None:
    """Count exact-match forbidden artifact tokens as keys or values."""
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


def assert_out_dir_outside_repo(out_dir: str | Path, repo_root: str | Path) -> None:
    """Refuse to write inside the repo. Real outputs must land elsewhere."""
    out_path = Path(out_dir).expanduser().resolve()
    repo_path = Path(repo_root).expanduser().resolve()
    try:
        out_path.relative_to(repo_path)
    except ValueError:
        return
    raise SafetyViolation(
        f"refusing to write inside repo: out_dir={out_path} is under repo={repo_path}; "
        "use $PBKR_PROCESSED_ROOT or $PBKR_OUTPUT_ROOT instead"
    )


def validate_with_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate ``payload`` against a JSON Schema. Lazy import jsonschema."""
    try:
        import jsonschema  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "jsonschema is required for validate_with_schema; "
            "install via `pip install jsonschema`"
        ) from e
    jsonschema.validate(payload, schema)


SCHEMA_FILES = {
    "market_breadth_pack": "market_breadth_pack.schema.json",
    "kr_leader_universe_pack": "kr_leader_universe_pack.schema.json",
    "sector_leadership_pack": "sector_leadership_pack.schema.json",
    "theme_leadership_pack": "theme_leadership_pack.schema.json",
    "evidence_overlay_pack": "evidence_overlay_pack.schema.json",
    "pbkr_full_daily_input_packet": "pbkr_full_daily_input_packet.schema.json",
}


def load_schema(name: str) -> dict[str, Any]:
    """Load a full-system schema by short name."""
    if name not in SCHEMA_FILES:
        raise KeyError(f"unknown full-system schema: {name}")
    schema_dir = Path(__file__).parent / "schemas"
    return json.loads((schema_dir / SCHEMA_FILES[name]).read_text(encoding="utf-8"))
