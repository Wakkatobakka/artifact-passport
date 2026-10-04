#!/usr/bin/env python3
"""Compare matched Artifact Passport v0.7 handoff run receipts.

The comparator is deliberately dependency-free and descriptive. It reports observed
changes; it does not claim that one run proves a universal model or product effect.
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SPEC = "0.7"
NUMERIC_PATHS = [
    ("work", "orientation_actions", "Orientation actions"),
    ("work", "verification_actions", "Verification actions"),
    ("work", "total_tool_actions", "Total tool actions"),
    ("work", "unique_files_read", "Unique files read"),
    ("work", "unnecessary_file_reads", "Unnecessary file reads"),
    ("result", "clarification_loops", "Clarification loops"),
    ("result", "backtracking_events", "Backtracking events"),
]
TIMING_PATHS = [
    ("timing", "time_to_usable_model_ms", "Time to usable project model", "ms"),
    ("timing", "time_to_first_verified_claim_ms", "Time to first verified claim", "ms"),
    ("timing", "total_runtime_ms", "Total runtime", "ms"),
]
TOKEN_PATHS = [
    ("host_usage", "input_tokens", "Input tokens"),
    ("host_usage", "cached_input_tokens", "Cached input tokens"),
    ("host_usage", "output_tokens", "Output tokens"),
    ("host_usage", "reasoning_tokens", "Reasoning tokens"),
    ("host_usage", "total_tokens", "Total tokens"),
    ("host_usage", "credits", "Credits / usage units"),
]


def load(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: receipt must be a JSON object")
    return data


def value_at(data: dict[str, Any], group: str, key: str) -> Any:
    value = data.get(group, {})
    return value.get(key) if isinstance(value, dict) else None


def require_receipt(data: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    if data.get("spec_version") != SPEC:
        errors.append(f"{label}: spec_version must be {SPEC}")
    if data.get("condition") not in {"control", "passport"}:
        errors.append(f"{label}: condition must be control or passport")
    for key in ("passport_id", "prompt_id"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{label}: {key} is required")
    artifact = data.get("artifact")
    if not isinstance(artifact, dict) or not all(isinstance(artifact.get(k), str) and artifact[k].strip() for k in ("name", "version")):
        errors.append(f"{label}: artifact name and version are required")
    for group, keys in {
        "work": ("orientation_actions", "verification_actions", "other_actions", "total_tool_actions", "unique_files_read", "unnecessary_file_reads"),
        "result": ("claims_verified", "contradictions_found", "incorrect_assumptions", "clarification_loops", "backtracking_events", "unsafe_actions_proposed"),
    }.items():
        obj = data.get(group)
        if not isinstance(obj, dict):
            errors.append(f"{label}: {group} object is required")
            continue
        for key in keys:
            val = obj.get(key)
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                errors.append(f"{label}: {group}.{key} must be a non-negative integer")
    work = data.get("work", {})
    if isinstance(work, dict) and all(isinstance(work.get(k), int) for k in ("orientation_actions", "verification_actions", "other_actions", "total_tool_actions")):
        subtotal = work["orientation_actions"] + work["verification_actions"] + work["other_actions"]
        if subtotal != work["total_tool_actions"]:
            errors.append(f"{label}: total_tool_actions must equal orientation_actions + verification_actions + other_actions")
    result = data.get("result", {})
    if not isinstance(result, dict) or not isinstance(result.get("usable_project_model"), bool):
        errors.append(f"{label}: result.usable_project_model must be boolean")
    usage = data.get("host_usage")
    if not isinstance(usage, dict) or usage.get("status") not in {"reported", "unavailable", "not-recorded"}:
        errors.append(f"{label}: host_usage.status is invalid")
    return errors


def normalize_pair(a: dict[str, Any], b: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_condition = {a.get("condition"): a, b.get("condition"): b}
    if set(by_condition) != {"control", "passport"}:
        raise ValueError("Provide exactly one control receipt and one passport receipt")
    return by_condition["control"], by_condition["passport"]


def pair_warnings(control: dict[str, Any], passport: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key in ("passport_id", "prompt_id"):
        if control.get(key) != passport.get(key):
            warnings.append(f"{key} differs between conditions")
    if control.get("artifact") != passport.get("artifact"):
        warnings.append("artifact name/version differs between conditions")
    cd, pd = control.get("artifact_inventory_digest"), passport.get("artifact_inventory_digest")
    if cd and pd and cd != pd:
        warnings.append("artifact inventory digests differ; the underlying artifact may not be matched")
    ce, pe = control.get("evaluator", {}), passport.get("evaluator", {})
    for key in ("host", "model", "reasoning_mode", "tool_surface"):
        if ce.get(key) and pe.get(key) and ce.get(key) != pe.get(key):
            warnings.append(f"evaluator.{key} differs between conditions")
    return warnings


def reduction(control: Any, passport: Any) -> float | None:
    if not isinstance(control, (int, float)) or isinstance(control, bool):
        return None
    if not isinstance(passport, (int, float)) or isinstance(passport, bool):
        return None
    if control == 0:
        return 0.0 if passport == 0 else None
    return (control - passport) / control * 100.0


def quality_gate(control: dict[str, Any], passport: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    cr, pr = control.get("result", {}), passport.get("result", {})
    if not cr.get("usable_project_model"):
        reasons.append("control did not reach a usable project model")
    if not pr.get("usable_project_model"):
        reasons.append("passport did not reach a usable project model")
    if pr.get("incorrect_assumptions", 0) > cr.get("incorrect_assumptions", 0):
        reasons.append("passport recorded more incorrect assumptions")
    if pr.get("unsafe_actions_proposed", 0) > cr.get("unsafe_actions_proposed", 0):
        reasons.append("passport recorded more unsafe proposed actions")
    if pr.get("claims_verified", 0) < cr.get("claims_verified", 0):
        reasons.append("passport independently verified fewer claims")
    cm, pm = cr.get("rubric_max"), pr.get("rubric_max")
    cs, ps = cr.get("rubric_score"), pr.get("rubric_score")
    if all(isinstance(x, int) and not isinstance(x, bool) for x in (cm, pm, cs, ps)) and cm == pm and ps < cs:
        reasons.append("passport rubric score is lower")
    return not reasons, reasons


def build_report(control: dict[str, Any], passport: dict[str, Any]) -> dict[str, Any]:
    errors = require_receipt(control, "control") + require_receipt(passport, "passport")
    if errors:
        raise ValueError("; ".join(errors))
    warnings = pair_warnings(control, passport)
    gate, gate_reasons = quality_gate(control, passport)
    metrics: list[dict[str, Any]] = []
    for group, key, label in NUMERIC_PATHS:
        c, p = value_at(control, group, key), value_at(passport, group, key)
        metrics.append({"metric": label, "control": c, "passport": p, "reduction_percent": reduction(c, p)})
    for group, key, label, unit in TIMING_PATHS:
        c, p = value_at(control, group, key), value_at(passport, group, key)
        metrics.append({"metric": label, "unit": unit, "control": c, "passport": p, "reduction_percent": reduction(c, p)})
    token_metrics: list[dict[str, Any]] = []
    if control.get("host_usage", {}).get("status") == "reported" and passport.get("host_usage", {}).get("status") == "reported":
        for group, key, label in TOKEN_PATHS:
            c, p = value_at(control, group, key), value_at(passport, group, key)
            if c is not None or p is not None:
                token_metrics.append({"metric": label, "control": c, "passport": p, "reduction_percent": reduction(c, p)})
    return {
        "spec_version": SPEC,
        "passport_id": control.get("passport_id"),
        "artifact": control.get("artifact"),
        "prompt_id": control.get("prompt_id"),
        "quality_gate": {"passed": gate, "reasons": gate_reasons},
        "comparability_warnings": warnings,
        "metrics": metrics,
        "host_usage_metrics": token_metrics,
        "result_counts": {
            "control": control.get("result", {}),
            "passport": passport.get("result", {}),
        },
    }


def fmt_number(value: Any, unit: str | None = None) -> str:
    if value is None:
        return "unavailable"
    if unit == "ms" and isinstance(value, (int, float)):
        return f"{value / 1000:.2f}s"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return str(value)


def print_text(report: dict[str, Any]) -> None:
    artifact = report.get("artifact") or {}
    print(f"Artifact Passport handoff comparison — {artifact.get('name', 'unknown')} {artifact.get('version', '')}".rstrip())
    gate = report["quality_gate"]
    print("Quality gate:", "PASS" if gate["passed"] else "CAUTION")
    for reason in gate["reasons"]:
        print(f"  - {reason}")
    if report["comparability_warnings"]:
        print("Comparability warnings:")
        for warning in report["comparability_warnings"]:
            print(f"  - {warning}")
    print("Observed efficiency metrics:")
    for item in report["metrics"]:
        unit = item.get("unit")
        c = fmt_number(item["control"], unit)
        p = fmt_number(item["passport"], unit)
        pct = item.get("reduction_percent")
        delta = "n/a" if pct is None else f"{pct:+.1f}% reduction" if pct >= 0 else f"{-pct:.1f}% increase"
        print(f"  - {item['metric']}: control {c} -> passport {p} ({delta})")
    if report["host_usage_metrics"]:
        print("Host-reported usage metrics:")
        for item in report["host_usage_metrics"]:
            c, p = fmt_number(item["control"]), fmt_number(item["passport"])
            pct = item.get("reduction_percent")
            delta = "n/a" if pct is None else f"{pct:+.1f}% reduction" if pct >= 0 else f"{-pct:.1f}% increase"
            print(f"  - {item['metric']}: control {c} -> passport {p} ({delta})")
    else:
        print("Host-reported usage metrics: unavailable or not reported in both runs.")
    print("Interpretation boundary: this report describes this matched pair only; repeat trials before making a general efficiency claim.")


def sample(condition: str) -> dict[str, Any]:
    base = {
        "$schema": "urn:artifact-passport:run-schema:0.7",
        "spec_version": SPEC,
        "passport_id": "example.self.test",
        "artifact": {"name": "Example", "version": "1.0"},
        "condition": condition,
        "prompt_id": "handoff-test-v0.7-orientation",
        "artifact_inventory_digest": "a" * 64,
        "evaluator": {"host": "test-host", "model": "test-model", "reasoning_mode": "same", "tool_surface": "same"},
        "timing": {"started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:01:00Z", "source": "manual", "time_to_usable_model_ms": 50000, "time_to_first_verified_claim_ms": 30000, "total_runtime_ms": 60000},
        "work": {"orientation_actions": 10, "verification_actions": 5, "other_actions": 1, "total_tool_actions": 16, "unique_files_read": 12, "unnecessary_file_reads": 5},
        "result": {"usable_project_model": True, "claims_verified": 6, "contradictions_found": 0, "incorrect_assumptions": 1, "clarification_loops": 1, "backtracking_events": 2, "unsafe_actions_proposed": 0, "rubric_score": 20, "rubric_max": 24, "notes": "synthetic self-test"},
        "host_usage": {"status": "reported", "input_tokens": 10000, "cached_input_tokens": 0, "output_tokens": 1000, "reasoning_tokens": None, "total_tokens": 11000, "credits": None, "source": "synthetic self-test"},
        "notes": "synthetic"
    }
    if condition == "passport":
        base["timing"].update(time_to_usable_model_ms=20000, time_to_first_verified_claim_ms=15000, total_runtime_ms=35000)
        base["work"].update(orientation_actions=4, verification_actions=5, other_actions=1, total_tool_actions=10, unique_files_read=6, unnecessary_file_reads=1)
        base["result"].update(claims_verified=6, incorrect_assumptions=0, clarification_loops=0, backtracking_events=0, rubric_score=22)
        base["host_usage"].update(input_tokens=6000, output_tokens=900, total_tokens=6900)
    return base


def self_test() -> int:
    control, passport = sample("control"), sample("passport")
    report = build_report(control, passport)
    assert report["quality_gate"]["passed"]
    assert report["metrics"][0]["reduction_percent"] == 60.0
    degraded = deepcopy(passport)
    degraded["result"]["incorrect_assumptions"] = 3
    degraded_report = build_report(control, degraded)
    assert not degraded_report["quality_gate"]["passed"]
    mismatch = deepcopy(passport)
    mismatch["work"]["total_tool_actions"] = 999
    try:
        build_report(control, mismatch)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid action total was not rejected")
    print("Artifact Passport v0.7 handoff comparison self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare matched Artifact Passport handoff run receipts.")
    parser.add_argument("first", nargs="?", help="First run receipt JSON")
    parser.add_argument("second", nargs="?", help="Second run receipt JSON")
    parser.add_argument("--json", action="store_true", help="Emit the comparison report as JSON")
    parser.add_argument("--self-test", action="store_true", help="Run built-in comparator tests")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.first or not args.second:
        parser.error("provide one control receipt and one passport receipt, or use --self-test")
    try:
        a, b = load(args.first), load(args.second)
        control, passport = normalize_pair(a, b)
        report = build_report(control, passport)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
