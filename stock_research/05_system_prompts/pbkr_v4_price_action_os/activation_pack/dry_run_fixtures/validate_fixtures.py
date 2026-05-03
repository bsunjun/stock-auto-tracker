#!/usr/bin/env python3
"""PBKR v4 anonymized dry-run fixture validator.

Read-only. Standard library only. No network. No subprocess. No file
write. Educational use only. Does not authorize execution.

What this script does
---------------------
- Lists every ``*.fixture.json`` in the directory containing this
  script.
- Loads PR #52 schemas from the sibling ``../../schemas/`` directory.
- For each fixture:
  * confirms the JSON parses,
  * confirms ``schema_refs`` is present and only references repo-
    relative paths,
  * for each ``artifacts.<key>`` whose key matches a known schema
    prefix, runs a minimal Draft-07-subset shape check against that
    schema,
  * runs global safety + anonymization audits.

What this script does NOT do
----------------------------
- It does not connect to a network, brokerage, market-data feed, or
  any external API.
- It does not read or modify engine code, parsers, bridges, builders,
  emitters, ticker maps, Kiwoom adapters, WiseReport adapters, or
  Drive scripts.
- It does not write any file.
- It does not invoke any subprocess.
- It does not mutate fixtures or schemas.
- It does not produce trade signals, recommendations, or order
  intents.

Output
------
Print-only. ``OVERALL: PASS`` (exit 0) or ``OVERALL: FAIL`` (exit 1).
"""

import json
import re
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
SCHEMAS_DIR = THIS_DIR.parent.parent / "schemas"

ALLOWED_NAMES = {"Candidate A", "Candidate B", "Candidate C"}
ALLOWED_DATE_PREFIX = "2099-"

# Match an artifact key (in fixture.artifacts) to a schema by prefix.
# Order matters: longest-match-first to avoid false matches between
# similar prefixes.
ARTIFACT_PREFIX_TO_SCHEMA = [
    ("news_grounding_pack", "news_grounding_pack.schema.json"),
    ("daily_focus_list",    "daily_focus_list.schema.json"),
    ("position_update",     "position_update.schema.json"),
    ("snipe_candidate",     "snipe_candidate.schema.json"),
    ("watchlist_item",      "watchlist_item.schema.json"),
    ("trade_ticket",        "trade_ticket.schema.json"),
    ("market_cycle",        "market_cycle.schema.json"),
    ("audit_pack",          "audit_pack.schema.json"),
    ("weekly_review",       "weekly_review.schema.json"),
]

FORBIDDEN_SUBSTRINGS = [
    "order_id",
    "fill_price",
    "broker",
    "kiwoom",
    "wisereport",
    "drive",
    "api_key",
    "token",
    "password",
]

SIX_DIGIT_RE = re.compile(r"\b\d{6}\b")
LONG_NUMERIC_RE = re.compile(r"\b\d{10,}\b")
URL_RE = re.compile(r"https?://", re.IGNORECASE)
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


# --------------------------------------------------------------------
# Schema loading
# --------------------------------------------------------------------

def load_schemas():
    """Load all known schemas. Returns {filename: parsed_dict}."""
    schemas = {}
    for _, fname in ARTIFACT_PREFIX_TO_SCHEMA:
        path = SCHEMAS_DIR / fname
        if path.exists():
            schemas[fname] = json.loads(path.read_text(encoding="utf-8"))
    return schemas


def match_artifact_to_schema(art_key, schemas):
    """Resolve an artifact key against the known schema prefix table.

    Returns ``(schema_dict, expected_filename, prefix_matched)``:

    - ``prefix_matched`` is True iff the artifact key matches a known
      prefix in ``ARTIFACT_PREFIX_TO_SCHEMA``.
    - ``schema_dict`` is the loaded schema, or ``None`` if the
      schema file was not found on disk (the caller must treat this
      as a hard failure when ``prefix_matched`` is True).
    - ``expected_filename`` is the schema filename that the prefix
      maps to, or ``None`` when no prefix matches.
    """
    for prefix, fname in ARTIFACT_PREFIX_TO_SCHEMA:
        if art_key == prefix or art_key.startswith(prefix + "_"):
            return (schemas.get(fname), fname, True)
    return (None, None, False)


# --------------------------------------------------------------------
# Minimal Draft-07-subset shape validator
# --------------------------------------------------------------------

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def _type_check(value, expected):
    """Strict type check; rejects bool-as-integer/number."""
    py_type = _TYPE_MAP.get(expected)
    if py_type is None:
        return True
    if expected in ("integer", "number") and isinstance(value, bool):
        return False
    if expected == "boolean" and not isinstance(value, bool):
        return False
    return isinstance(value, py_type)


def validate_against_schema(data, schema, path, issues):
    """Walk a fixture artifact against a JSON Schema (subset).

    Implements: type, const, enum, required, additionalProperties,
    properties, items, minItems, maxItems. Other keywords are ignored.
    """
    if not isinstance(schema, dict):
        return

    # type
    if "type" in schema:
        expected = schema["type"]
        if isinstance(expected, list):
            if not any(_type_check(data, t) for t in expected):
                issues.append(f"{path}: type must be one of {expected}")
        else:
            if not _type_check(data, expected):
                issues.append(
                    f"{path}: type must be {expected}, "
                    f"got {type(data).__name__}"
                )

    # const
    if "const" in schema and data != schema["const"]:
        issues.append(
            f"{path}: const must be {schema['const']!r}, got {data!r}"
        )

    # enum
    if "enum" in schema and data not in schema["enum"]:
        issues.append(
            f"{path}: enum must be one of {schema['enum']}, "
            f"got {data!r}"
        )

    # object
    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                issues.append(
                    f"{path}: required field '{req}' missing"
                )
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for k in data:
                if k not in props:
                    issues.append(
                        f"{path}: additional property '{k}' "
                        f"not allowed"
                    )
        for k, v in data.items():
            if k in props:
                validate_against_schema(
                    v, props[k], f"{path}.{k}", issues
                )

    # array
    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            issues.append(
                f"{path}: minItems {schema['minItems']}, "
                f"got {len(data)}"
            )
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            issues.append(
                f"{path}: maxItems {schema['maxItems']}, "
                f"got {len(data)}"
            )
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                validate_against_schema(
                    item, items_schema, f"{path}[{i}]", issues
                )


# --------------------------------------------------------------------
# Global safety + anonymization audits
# --------------------------------------------------------------------

def _walk_kv(obj, path=""):
    """Yield (path, key, value) for each k,v anywhere in obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (path, k, v)
            yield from _walk_kv(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_kv(v, f"{path}[{i}]")


def _walk_strings(obj, path=""):
    """Yield (path, string) for each string value anywhere in obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield (path, obj)


def safety_audits(data, issues):
    """Apply signal-safety, anonymization, and leak audits."""
    for path, k, v in _walk_kv(data):
        if k == "direct_trade_signal" and v is not False:
            issues.append(
                f"{path}.{k}: must be false, got {v!r}"
            )
        if k == "trade_signal" and v not in (None, False):
            issues.append(
                f"{path}.{k}: must be null or false, got {v!r}"
            )
        if k == "automatic_execution_allowed" and v is not False:
            issues.append(
                f"{path}.{k}: must be false, got {v!r}"
            )
        if k == "human_gate_required" and v is not True:
            issues.append(
                f"{path}.{k}: must be true, got {v!r}"
            )
        if k == "operator_decision" and v == "execute":
            issues.append(
                f"{path}.{k}: 'execute' is forbidden in fixtures"
            )
        if k == "name" and isinstance(v, str) and v not in ALLOWED_NAMES:
            issues.append(
                f"{path}.{k}: name must be one of "
                f"{sorted(ALLOWED_NAMES)}, got {v!r}"
            )

    for path, s in _walk_strings(data):
        # Date prefix check
        if DATE_PREFIX_RE.match(s) and not s.startswith(ALLOWED_DATE_PREFIX):
            issues.append(
                f"{path}: date prefix not '2099-': {s!r}"
            )
        # Forbidden substrings (case-insensitive)
        s_lower = s.lower()
        for sub in FORBIDDEN_SUBSTRINGS:
            if sub in s_lower:
                issues.append(
                    f"{path}: forbidden substring '{sub}' in "
                    f"value {s!r}"
                )
        # 6-digit numeric pattern (likely real KR ticker)
        if SIX_DIGIT_RE.search(s):
            issues.append(
                f"{path}: 6-digit numeric pattern in value {s!r}"
            )
        # Long numeric pattern (DART rcpNo-like)
        if LONG_NUMERIC_RE.search(s):
            issues.append(
                f"{path}: long numeric pattern (>=10 digits) "
                f"in value {s!r}"
            )
        # URL
        if URL_RE.search(s):
            issues.append(
                f"{path}: URL pattern in value {s!r}"
            )


# --------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------

def main():
    fixture_files = sorted(THIS_DIR.glob("*.fixture.json"))
    if not fixture_files:
        print("VALIDATOR: no fixture files found in current directory.")
        return 1

    schemas = load_schemas()
    if not schemas:
        print(
            "VALIDATOR: no schemas found at "
            + str(SCHEMAS_DIR)
        )
        return 1

    overall_pass = True
    for fpath in fixture_files:
        issues = []
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"FAIL {fpath.name}: JSON parse error: {exc}")
            overall_pass = False
            continue

        # 1. schema_refs presence + repo-relative + file existence
        refs = data.get("schema_refs", [])
        if not isinstance(refs, list) or not refs:
            issues.append("schema_refs missing or empty")
        else:
            for ref in refs:
                if not isinstance(ref, str) or not ref.startswith("../"):
                    issues.append(
                        f"schema_refs entry not a repo-relative "
                        f"path: {ref!r}"
                    )
                    continue
                ref_path = THIS_DIR / ref
                if not ref_path.exists():
                    issues.append(
                        f"schema_refs entry points to a non-existent "
                        f"file: {ref!r}"
                    )

        # 2. validate each artifact against the matched schema
        artifacts = data.get("artifacts", {})
        if not isinstance(artifacts, dict):
            issues.append("artifacts must be an object")
        else:
            for art_key, art_payload in artifacts.items():
                schema, expected_fname, matched = (
                    match_artifact_to_schema(art_key, schemas)
                )
                if matched and schema is None:
                    # Prefix matched a known artifact type, but the
                    # schema file is missing on disk. Hard failure:
                    # silently skipping shape validation here would
                    # let fixtures be reported valid for an artifact
                    # type whose schema vanished or was renamed.
                    issues.append(
                        f"artifacts.{art_key}: matched schema "
                        f"prefix but expected schema file "
                        f"{expected_fname!r} not found in "
                        f"{SCHEMAS_DIR}"
                    )
                elif schema is not None:
                    validate_against_schema(
                        art_payload,
                        schema,
                        f"artifacts.{art_key}",
                        issues,
                    )

        # 3. global safety + anonymization audits
        safety_audits(data, issues)

        if issues:
            print(f"FAIL {fpath.name}:")
            for issue in issues:
                print(f"  - {issue}")
            overall_pass = False
        else:
            print(f"PASS {fpath.name}")

    print("---")
    print(f"checked: {len(fixture_files)} fixtures")
    if overall_pass:
        print("OVERALL: PASS")
        return 0
    print("OVERALL: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
