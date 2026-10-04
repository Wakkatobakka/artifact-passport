#!/usr/bin/env python3
"""Dependency-free validator for Artifact Passport, Handoff, and Run Receipt 0.7.

This validates the v0.7 core contracts and additional safety, clarity, and relationship semantics. The JSON
Schema remains the normative structural definition.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


REQUIRED_TOP = {
    "spec_version",
    "passport_id",
    "artifact",
    "intent",
    "operation",
    "structure",
    "constraints",
    "procedures",
    "verification",
    "authority",
    "review",
    "handoff",
}
ALLOWED_TOP = REQUIRED_TOP | {"$schema", "provenance", "intake", "unresolved", "extensions", "artifact_fingerprint"}
KINDS = {"application", "document", "dataset", "media", "model", "package", "source-code", "website", "workflow", "other"}
NETWORK_POLICIES = {"forbidden", "optional", "required"}
CLASSIFICATIONS = {"public", "internal", "confidential", "restricted", "mixed", "unspecified"}
METHODS = {"command", "inspection", "interaction", "comparison", "other"}
REVIEW_STATUSES = {"ai-draft", "owner-reviewed", "verified"}
HANDLING_POLICIES = {"yes", "no", "ask-owner"}
SECRET_KEY_RE = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|credential)", re.I)
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]+$")
CHECK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VAGUE_RE = re.compile(
    r"\b(?:i\s*(?:do not|don't|dont)\s*know|idk|not sure|unknown|uh+|whatever|lmao|lol|positive vibes?|if this works?|can'?t handle the truth|didn'?t understand)\b",
    re.I,
)


def suggested_file_role(raw_path: str, inventory: list[str]) -> str:
    """Return a conservative, reviewable role suggestion from a filename."""
    low = raw_path.lower()
    base = low.rsplit("/", 1)[-1]
    has_modified_bin = any(
        item.lower().endswith(".bin") and re.search(r"wakka|mod|patch|probe|output", item, re.I)
        for item in inventory
    )
    if re.search(r"\.(cmd|bat)$", low):
        return "entry-point"
    if re.search(r"\.(ps1|py|js|ts|sh)$", low):
        return "editable-source"
    if low.endswith(".cue"):
        return "generated-output"
    if low.endswith(".bin") and re.search(r"wakka|mod|patch|probe|output", low):
        return "generated-output"
    if low.endswith(".bin") and has_modified_bin:
        return "protected-input"
    if re.search(r"(?:build|test|verify).*(?:log|txt)$", base):
        return "evidence"
    if base.startswith("readme"):
        return "instructions"
    return "unknown"


def inventory_match(raw_path: str, inventory: list[str]) -> bool:
    path = raw_path.rstrip("/")
    return not inventory or raw_path in inventory or any(item.startswith(path + "/") for item in inventory)


def relationship_warnings(data: dict[str, Any], result: "Validation", inventory: list[str]) -> None:
    """Check whether individually valid answers agree with one another and with intake evidence."""
    artifact = data.get("artifact", {})
    intent = data.get("intent", {})
    operation = data.get("operation", {})
    structure = data.get("structure", {})
    procedures = data.get("procedures", {})
    handoff = data.get("handoff", {})
    entries = operation.get("entry_points", [])
    groups = [
        ("$.operation.entry_points", entries),
        ("$.structure.source_of_truth", structure.get("source_of_truth", [])),
        ("$.structure.generated_outputs", structure.get("generated_outputs", [])),
        ("$.structure.protected_items", structure.get("protected_items", [])),
    ]
    if inventory:
        for field, items in groups:
            for item in items:
                raw_path = item.get("path") if isinstance(item, dict) else None
                if is_nonempty(raw_path) and not inventory_match(raw_path, inventory):
                    result.warn(field, f"declared path does not match intake inventory: {raw_path}")
    start_here = handoff.get("start_here", "")
    if inventory and re.search(r"\.[A-Za-z0-9]{1,6}\b", start_here) and not any(item in start_here for item in inventory):
        result.warn("$.handoff.start_here", "appears to name a file that is not in the intake inventory")
    if artifact.get("version", "").lower() == "unversioned":
        result.warn("$.artifact.version", "a detected version was not confirmed")
    if artifact.get("kind") == "other" and any(re.search(r"\.(cmd|bat|ps1|py|js|ts|sh)$", item, re.I) for item in inventory):
        result.warn("$.artifact.kind", "runnable or editable logic was detected; consider package, workflow, or source-code")
    if any(re.search(r"(?:should|must|does)\s+not\s+(?:crash|fail)|should not fail to launch", item, re.I) for item in intent.get("out_of_scope", [])):
        result.warn("$.intent.out_of_scope", "an item sounds like a success or safety check rather than an exclusion")
    source_paths = [item.get("path", "") for item in structure.get("source_of_truth", []) if isinstance(item, dict)]
    if any(suggested_file_role(item, inventory) in {"entry-point", "protected-input", "generated-output"} for item in source_paths):
        result.warn("$.structure.source_of_truth", "at least one editable source looks like a launcher, protected input, or output")
    likely_sources = [item for item in inventory if suggested_file_role(item, inventory) == "editable-source"]
    missing_sources = [item for item in likely_sources if item not in source_paths]
    if missing_sources:
        result.warn("$.structure.source_of_truth", "likely editable logic is not listed as source of truth: " + ", ".join(missing_sources))
    checks = data.get("verification", {}).get("checks", [])
    generic = lambda check: re.search(r"fulfills its owner-confirmed purpose|every confirmed success criterion remains true", json.dumps(check), re.I)
    if checks and not any(not generic(check) and is_nonempty(check.get("description")) and is_nonempty(check.get("expected")) for check in checks if isinstance(check, dict)):
        result.warn("$.verification.checks", "verification is generic; name an action and an observable expected result")
    if not any(procedures.get(key) for key in ("setup", "edit", "build", "release")):
        result.warn("$.procedures", "setup, edit, build, and release steps are empty")
    if re.search(r"requires owner confirmation", operation.get("network_notes", ""), re.I):
        result.warn("$.operation.network_notes", "still says owner confirmation is required")
    if any(re.search(r"confirm", entry.get("role", ""), re.I) for entry in entries if isinstance(entry, dict)):
        result.warn("$.operation.entry_points", "entry-point role still says confirmation is required")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")


def is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def object_at(parent: Any, key: str, result: Validation, path: str = "$", required: bool = True) -> dict[str, Any]:
    value = parent.get(key) if isinstance(parent, dict) else None
    if value is None and not required:
        return {}
    if not isinstance(value, dict):
        result.error(f"{path}.{key}", "must be an object")
        return {}
    return value


def require_strings(obj: dict[str, Any], keys: list[str], result: Validation, path: str) -> None:
    for key in keys:
        if not is_nonempty(obj.get(key)):
            result.error(f"{path}.{key}", "must be a non-empty string")


def string_list(obj: dict[str, Any], key: str, result: Validation, path: str, minimum: int = 0) -> list[str]:
    value = obj.get(key)
    target = f"{path}.{key}"
    if not isinstance(value, list):
        result.error(target, "must be an array")
        return []
    if len(value) < minimum:
        result.error(target, f"must contain at least {minimum} item(s)")
    seen: set[str] = set()
    valid: list[str] = []
    for index, item in enumerate(value):
        if not is_nonempty(item):
            result.error(f"{target}[{index}]", "must be a non-empty string")
        elif item in seen:
            result.error(f"{target}[{index}]", "duplicates an earlier item")
        else:
            seen.add(item)
            valid.append(item)
    return valid


def date_time(value: Any, result: Validation, path: str) -> None:
    if not is_nonempty(value):
        result.error(path, "must be an RFC 3339 date-time string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        result.error(path, "is not a valid RFC 3339-style date-time")


def safe_relative_path(value: Any, result: Validation, path: str) -> None:
    if not is_nonempty(value):
        result.error(path, "must be a non-empty package-relative path")
        return
    if "\\" in value:
        result.warn(path, "uses backslashes; portable package paths should use forward slashes")
    candidate = PurePosixPath(value.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        result.error(path, "must not be absolute or escape the package root")


def validate_path_items(items: Any, result: Validation, path: str, minimum: int = 0) -> list[str]:
    if not isinstance(items, list):
        result.error(path, "must be an array")
        return []
    if len(items) < minimum:
        result.error(path, f"must contain at least {minimum} item(s)")
    paths: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            result.error(item_path, "must be an object")
            continue
        require_strings(item, ["path", "role"], result, item_path)
        if "path" in item:
            safe_relative_path(item["path"], result, f"{item_path}.path")
            if isinstance(item["path"], str):
                paths.append(item["path"])
    return paths


def scan_secret_keys(value: Any, result: Validation, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            measurement_counter = path == "$.host_usage" and key in {"input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens"}
            if SECRET_KEY_RE.search(key) and not measurement_counter:
                result.error(child_path, "secret-bearing fields are prohibited; reference a secure mechanism instead")
            scan_secret_keys(child, result, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_secret_keys(child, result, f"{path}[{index}]")


def clarity_warning(value: Any, result: Validation, path: str, minimum: int = 3) -> None:
    """Flag likely placeholders without claiming to judge semantic truth."""
    if isinstance(value, str) and value.strip() and (len(value.strip()) < minimum or VAGUE_RE.search(value)):
        result.warn(path, "looks like a placeholder, uncertainty marker, or process note; clarify before handoff")


def validate_passport(data: Any, package_root: Path | None = None) -> Validation:
    result = Validation()
    if not isinstance(data, dict):
        result.error("$", "passport must be a JSON object")
        return result

    missing = sorted(REQUIRED_TOP - data.keys())
    unknown = sorted(data.keys() - ALLOWED_TOP)
    for key in missing:
        result.error("$", f"missing required property '{key}'")
    for key in unknown:
        result.error(f"$.{key}", "unknown top-level property; use a namespaced extensions entry")

    if data.get("spec_version") != "0.7":
        result.error("$.spec_version", "must equal '0.7'")
    passport_id = data.get("passport_id")
    if not is_nonempty(passport_id) or len(passport_id) < 8 or not ID_RE.fullmatch(passport_id):
        result.error("$.passport_id", "must be at least 8 characters and use letters, digits, '.', '_', ':', or '-'")

    artifact = object_at(data, "artifact", result)
    require_strings(artifact, ["name", "version", "kind", "description", "updated_at"], result, "$.artifact")
    if artifact.get("kind") not in KINDS:
        result.error("$.artifact.kind", f"must be one of {', '.join(sorted(KINDS))}")
    if "updated_at" in artifact:
        date_time(artifact["updated_at"], result, "$.artifact.updated_at")
    if "created_at" in artifact:
        date_time(artifact["created_at"], result, "$.artifact.created_at")
    if "tags" in artifact:
        string_list(artifact, "tags", result, "$.artifact")

    intent = object_at(data, "intent", result)
    require_strings(intent, ["purpose"], result, "$.intent")
    string_list(intent, "audiences", result, "$.intent", 1)
    string_list(intent, "success_criteria", result, "$.intent", 1)
    if "out_of_scope" in intent:
        string_list(intent, "out_of_scope", result, "$.intent")

    operation = object_at(data, "operation", result)
    entries = operation.get("entry_points")
    if not isinstance(entries, list) or not entries:
        result.error("$.operation.entry_points", "must contain at least one entry point")
        entries = []
    for index, entry in enumerate(entries):
        path = f"$.operation.entry_points[{index}]"
        if not isinstance(entry, dict):
            result.error(path, "must be an object")
            continue
        require_strings(entry, ["path", "role", "open_with"], result, path)
        if "path" in entry:
            safe_relative_path(entry["path"], result, f"{path}.path")
    string_list(operation, "environment", result, "$.operation", 1)
    if operation.get("network_policy") not in NETWORK_POLICIES:
        result.error("$.operation.network_policy", "must be forbidden, optional, or required")
    dependencies = operation.get("dependencies")
    if not isinstance(dependencies, list):
        result.error("$.operation.dependencies", "must be an array")
    else:
        for index, dep in enumerate(dependencies):
            path = f"$.operation.dependencies[{index}]"
            if not isinstance(dep, dict):
                result.error(path, "must be an object")
            else:
                require_strings(dep, ["name", "requirement", "purpose"], result, path)

    structure = object_at(data, "structure", result)
    source_paths = validate_path_items(structure.get("source_of_truth"), result, "$.structure.source_of_truth", 1)
    generated_paths = validate_path_items(structure.get("generated_outputs"), result, "$.structure.generated_outputs")
    validate_path_items(structure.get("protected_items"), result, "$.structure.protected_items")
    string_list(structure, "ignore", result, "$.structure")
    overlap = sorted(set(source_paths) & set(generated_paths))
    for item in overlap:
        result.error("$.structure", f"'{item}' cannot be both source of truth and generated output")

    constraints = object_at(data, "constraints", result)
    for key in ["allowed_actions", "must", "must_not", "preserve"]:
        string_list(constraints, key, result, "$.constraints", 1)
    if "data_classification" in constraints and constraints["data_classification"] not in CLASSIFICATIONS:
        result.error("$.constraints.data_classification", "contains an unsupported classification")
    data_handling = object_at(constraints, "data_handling", result, "$.constraints")
    if data_handling.get("may_leave_device") not in HANDLING_POLICIES:
        result.error("$.constraints.data_handling.may_leave_device", "must be yes, no, or ask-owner")
    string_list(data_handling, "approved_contexts", result, "$.constraints.data_handling")
    if not isinstance(data_handling.get("redaction_required"), bool):
        result.error("$.constraints.data_handling.redaction_required", "must be a boolean")

    procedures = object_at(data, "procedures", result)
    for key in ["setup", "edit", "build", "verify", "release", "recovery"]:
        string_list(procedures, key, result, "$.procedures")

    verification = object_at(data, "verification", result)
    checks = verification.get("checks")
    required_count = 0
    check_ids: set[str] = set()
    if not isinstance(checks, list) or not checks:
        result.error("$.verification.checks", "must contain at least one check")
        checks = []
    for index, check in enumerate(checks):
        path = f"$.verification.checks[{index}]"
        if not isinstance(check, dict):
            result.error(path, "must be an object")
            continue
        require_strings(check, ["id", "description", "expected"], result, path)
        check_id = check.get("id")
        if is_nonempty(check_id):
            if not CHECK_ID_RE.fullmatch(check_id):
                result.error(f"{path}.id", "contains unsupported characters")
            if check_id in check_ids:
                result.error(f"{path}.id", "duplicates an earlier check id")
            check_ids.add(check_id)
        if check.get("method") is not None and check.get("method") not in METHODS:
            result.error(f"{path}.method", "contains an unsupported verification method")
        if not isinstance(check.get("required"), bool):
            result.error(f"{path}.required", "must be a boolean")
        elif check["required"]:
            required_count += 1
        if "command" in check and check.get("method") != "command":
            result.warn(f"{path}.command", "is present but method is not 'command'")
    if checks and required_count == 0:
        result.error("$.verification.checks", "must include at least one required check")
    if "last_verified" in verification:
        last = object_at(verification, "last_verified", result, "$.verification")
        require_strings(last, ["at", "by", "result"], result, "$.verification.last_verified")
        if "at" in last:
            date_time(last["at"], result, "$.verification.last_verified.at")
        if last.get("result") not in {"passed", "failed", "partial"}:
            result.error("$.verification.last_verified.result", "must be passed, failed, or partial")

    authority = object_at(data, "authority", result)
    require_strings(authority, ["owner", "change_policy"], result, "$.authority")
    string_list(authority, "approvers", result, "$.authority", 1)

    review = object_at(data, "review", result)
    if review.get("status") not in REVIEW_STATUSES:
        result.error("$.review.status", "must be ai-draft, owner-reviewed, or verified")
    if review.get("status") in {"owner-reviewed", "verified"}:
        require_strings(review, ["reviewed_by", "reviewed_at"], result, "$.review")
        if "reviewed_at" in review:
            date_time(review["reviewed_at"], result, "$.review.reviewed_at")
    elif review.get("status") == "ai-draft":
        result.warn("$.review.status", "claims remain an AI draft until an owner reviews them")

    fingerprint = data.get("artifact_fingerprint")
    if fingerprint is not None:
        if not isinstance(fingerprint, dict):
            result.error("$.artifact_fingerprint", "must be an object")
        else:
            require_strings(fingerprint, ["algorithm", "inventory_digest", "generated_at"], result, "$.artifact_fingerprint")
            if fingerprint.get("algorithm") != "sha256-inventory-v1":
                result.error("$.artifact_fingerprint.algorithm", "must equal sha256-inventory-v1")
            if not re.fullmatch(r"[a-fA-F0-9]{64}", str(fingerprint.get("inventory_digest", ""))):
                result.error("$.artifact_fingerprint.inventory_digest", "must be a 64-character SHA-256 digest")
            for key in ("file_count", "total_size_bytes"):
                if not isinstance(fingerprint.get(key), int) or fingerprint[key] < 0:
                    result.error(f"$.artifact_fingerprint.{key}", "must be a non-negative integer")
            if "generated_at" in fingerprint:
                date_time(fingerprint["generated_at"], result, "$.artifact_fingerprint.generated_at")

    handoff = object_at(data, "handoff", result)
    require_strings(handoff, ["start_here"], result, "$.handoff")
    string_list(handoff, "safe_first_actions", result, "$.handoff", 1)
    string_list(handoff, "known_limitations", result, "$.handoff")
    string_list(handoff, "open_questions", result, "$.handoff")

    unresolved = data.get("unresolved", [])
    if not isinstance(unresolved, list):
        result.error("$.unresolved", "must be an array")
    else:
        for index, item in enumerate(unresolved):
            item_path = f"$.unresolved[{index}]"
            if not isinstance(item, dict):
                result.error(item_path, "must be an object")
            else:
                require_strings(item, ["field", "question"], result, item_path)
        if unresolved:
            result.warn("$.unresolved", f"{len(unresolved)} owner answer(s) are explicitly unresolved; passport is not handoff-ready")

    clarity_warning(artifact.get("description"), result, "$.artifact.description", 18)
    clarity_warning(intent.get("purpose"), result, "$.intent.purpose", 12)
    for index, value in enumerate(intent.get("audiences", [])):
        clarity_warning(value, result, f"$.intent.audiences[{index}]", 4)
    for index, value in enumerate(intent.get("success_criteria", [])):
        clarity_warning(value, result, f"$.intent.success_criteria[{index}]", 12)
    for index, entry in enumerate(entries):
        if isinstance(entry, dict):
            clarity_warning(entry.get("path"), result, f"$.operation.entry_points[{index}].path")
            clarity_warning(entry.get("open_with"), result, f"$.operation.entry_points[{index}].open_with")
    for index, value in enumerate(operation.get("environment", [])):
        clarity_warning(value, result, f"$.operation.environment[{index}]", 5)
    for index, item in enumerate(structure.get("source_of_truth", [])):
        if isinstance(item, dict):
            clarity_warning(item.get("path"), result, f"$.structure.source_of_truth[{index}].path")
    clarity_warning(authority.get("owner"), result, "$.authority.owner", 4)
    for index, value in enumerate(authority.get("approvers", [])):
        clarity_warning(value, result, f"$.authority.approvers[{index}]")
    clarity_warning(authority.get("change_policy"), result, "$.authority.change_policy", 12)

    intake_inventory: list[str] = []
    if "intake" in data:
        intake = object_at(data, "intake", result)
        require_strings(intake, ["created_at", "mode", "detected_type"], result, "$.intake")
        if "created_at" in intake:
            date_time(intake["created_at"], result, "$.intake.created_at")
        if intake.get("mode") not in {"json", "folder", "zip", "passport-migration", "passport-repair"}:
            result.error("$.intake.mode", "must be json, folder, zip, passport-migration, or passport-repair")
        intake_sources = intake.get("sources")
        if not isinstance(intake_sources, list) or not intake_sources:
            result.error("$.intake.sources", "must contain at least one source")
        else:
            for index, source in enumerate(intake_sources):
                source_path = f"$.intake.sources[{index}]"
                if not isinstance(source, dict):
                    result.error(source_path, "must be an object")
                else:
                    require_strings(source, ["name", "media_type", "role"], result, source_path)
                    if "size_bytes" in source and (not isinstance(source["size_bytes"], int) or source["size_bytes"] < 0):
                        result.error(f"{source_path}.size_bytes", "must be a non-negative integer")
        observations = intake.get("observations")
        unresolved_observations = 0
        if not isinstance(observations, list):
            result.error("$.intake.observations", "must be an array")
        else:
            for index, observation in enumerate(observations):
                observation_path = f"$.intake.observations[{index}]"
                if not isinstance(observation, dict):
                    result.error(observation_path, "must be an object")
                    continue
                require_strings(observation, ["field", "status"], result, observation_path)
                if "value" not in observation:
                    result.error(f"{observation_path}.value", "is required")
                if observation.get("status") not in {"extracted", "inferred", "owner-required"}:
                    result.error(f"{observation_path}.status", "contains an unsupported evidence state")
                elif observation.get("status") in {"inferred", "owner-required"} and observation.get("accepted") is not True and observation.get("reviewed") is not True:
                    unresolved_observations += 1
                if "accepted" in observation and not isinstance(observation["accepted"], bool):
                    result.error(f"{observation_path}.accepted", "must be a boolean")
                if "reviewed" in observation and not isinstance(observation["reviewed"], bool):
                    result.error(f"{observation_path}.reviewed", "must be a boolean")
                confidence = observation.get("confidence")
                if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1):
                    result.error(f"{observation_path}.confidence", "must be a number from 0 to 1")
        owner_questions = string_list(intake, "owner_questions", result, "$.intake")
        if "inventory" in intake:
            intake_inventory = string_list(intake, "inventory", result, "$.intake")
        candidates = intake.get("file_candidates", [])
        if not isinstance(candidates, list):
            result.error("$.intake.file_candidates", "must be an array")
        else:
            roles = {"passport", "handoff", "entry-point", "editable-source", "protected-input", "generated-output", "evidence", "instructions", "unknown"}
            for index, candidate in enumerate(candidates):
                candidate_path = f"$.intake.file_candidates[{index}]"
                if not isinstance(candidate, dict):
                    result.error(candidate_path, "must be an object")
                    continue
                require_strings(candidate, ["path", "role", "label"], result, candidate_path)
                if candidate.get("role") not in roles:
                    result.error(f"{candidate_path}.role", "contains an unsupported suggested role")
                confidence = candidate.get("confidence")
                if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
                    result.error(f"{candidate_path}.confidence", "must be a number from 0 to 1")
        unresolved = max(unresolved_observations, len(owner_questions))
        if unresolved:
            result.warn("$.intake", f"structurally valid but {unresolved} intake confirmation(s) remain")

    relationship_warnings(data, result, intake_inventory)

    extensions = data.get("extensions")
    if extensions is not None:
        if not isinstance(extensions, dict):
            result.error("$.extensions", "must be an object")
        else:
            for key in extensions:
                if not re.fullmatch(r"^[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)+$", key):
                    result.error(f"$.extensions.{key}", "extension keys must be namespaced")

    scan_secret_keys(data, result)

    if package_root:
        declared = []
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                declared.append(("entry point", entry["path"]))
        declared += [("source of truth", path) for path in source_paths]
        for role, raw_path in declared:
            candidate = package_root / raw_path
            if not candidate.exists():
                result.warn("$.structure", f"declared {role} does not exist under package root: {raw_path}")

    return result


def validate_handoff(data: Any) -> Validation:
    """Validate the small, frequently replaced current-state companion."""
    result = Validation()
    if not isinstance(data, dict):
        result.error("$", "handoff must be a JSON object")
        return result
    required = {"spec_version", "passport_id", "artifact", "updated_at", "review", "working_state", "context_snapshot", "context_routes", "open_questions"}
    for key in sorted(required - data.keys()):
        result.error("$", f"missing required property '{key}'")
    if data.get("spec_version") != "0.7":
        result.error("$.spec_version", "must equal '0.7'")
    passport_id = data.get("passport_id")
    if not is_nonempty(passport_id) or len(passport_id) < 8 or not ID_RE.fullmatch(passport_id):
        result.error("$.passport_id", "must identify its companion passport")
    artifact = object_at(data, "artifact", result)
    require_strings(artifact, ["name", "version"], result, "$.artifact")
    date_time(data.get("updated_at"), result, "$.updated_at")
    review = object_at(data, "review", result)
    if review.get("status") not in REVIEW_STATUSES:
        result.error("$.review.status", "must be ai-draft, owner-reviewed, or verified")
    if review.get("status") in {"owner-reviewed", "verified"}:
        require_strings(review, ["reviewed_by", "reviewed_at"], result, "$.review")
        if "reviewed_at" in review:
            date_time(review["reviewed_at"], result, "$.review.reviewed_at")
    working = object_at(data, "working_state", result)
    require_strings(working, ["current_status", "current_known_good", "current_objective", "recommended_next_move"], result, "$.working_state")
    attempts = working.get("failed_attempts")
    if not isinstance(attempts, list):
        result.error("$.working_state.failed_attempts", "must be an array")
    else:
        for index, attempt in enumerate(attempts):
            path = f"$.working_state.failed_attempts[{index}]"
            if not isinstance(attempt, dict):
                result.error(path, "must be an object")
            else:
                require_strings(attempt, ["summary", "outcome"], result, path)
                if "avoid_repeating" in attempt and not isinstance(attempt["avoid_repeating"], bool):
                    result.error(f"{path}.avoid_repeating", "must be a boolean")
    snapshot = object_at(data, "context_snapshot", result)
    for key in ["do_not_break", "decision_history", "known_uncertainties", "recent_delta"]:
        string_list(snapshot, key, result, "$.context_snapshot")
    if not isinstance(snapshot.get("recent_delta_from"), str):
        result.error("$.context_snapshot.recent_delta_from", "must be a string")
    routes = object_at(data, "context_routes", result)
    string_list(routes, "always_read", result, "$.context_routes", 1)
    string_list(routes, "avoid_by_default", result, "$.context_routes")
    by_task = routes.get("by_task")
    if not isinstance(by_task, list):
        result.error("$.context_routes.by_task", "must be an array")
    else:
        for index, route in enumerate(by_task):
            path = f"$.context_routes.by_task[{index}]"
            if not isinstance(route, dict):
                result.error(path, "must be an object")
            else:
                require_strings(route, ["task"], result, path)
                string_list(route, "read", result, path, 1)
    string_list(data, "open_questions", result, "$")
    scan_secret_keys(data, result)
    return result



def validate_run_receipt(data: Any) -> Validation:
    """Validate an optional observational handoff-efficiency run receipt."""
    result = Validation()
    if not isinstance(data, dict):
        result.error("$", "run receipt must be a JSON object")
        return result
    required = {"spec_version", "passport_id", "artifact", "condition", "prompt_id", "evaluator", "timing", "work", "result", "host_usage"}
    for key in sorted(required - data.keys()):
        result.error("$", f"missing required property '{key}'")
    if data.get("spec_version") != "0.7":
        result.error("$.spec_version", "must equal '0.7'")
    if data.get("condition") not in {"control", "passport"}:
        result.error("$.condition", "must be control or passport")
    passport_id = data.get("passport_id")
    if not is_nonempty(passport_id) or len(passport_id) < 8 or not ID_RE.fullmatch(passport_id):
        result.error("$.passport_id", "must identify the benchmarked passport")
    if not is_nonempty(data.get("prompt_id")):
        result.error("$.prompt_id", "must identify the exact benchmark prompt")
    artifact = object_at(data, "artifact", result)
    require_strings(artifact, ["name", "version"], result, "$.artifact")
    digest = data.get("artifact_inventory_digest")
    if digest is not None and not re.fullmatch(r"[a-fA-F0-9]{64}", str(digest)):
        result.error("$.artifact_inventory_digest", "must be null or a 64-character SHA-256 digest")
    evaluator = object_at(data, "evaluator", result)
    require_strings(evaluator, ["host", "model"], result, "$.evaluator")
    timing = object_at(data, "timing", result)
    require_strings(timing, ["started_at", "completed_at", "source"], result, "$.timing")
    if "started_at" in timing:
        date_time(timing["started_at"], result, "$.timing.started_at")
    if "completed_at" in timing:
        date_time(timing["completed_at"], result, "$.timing.completed_at")
    if timing.get("source") not in {"host-reported", "manual", "estimated", "unavailable"}:
        result.error("$.timing.source", "must be host-reported, manual, estimated, or unavailable")
    for key in ["time_to_usable_model_ms", "time_to_first_verified_claim_ms", "total_runtime_ms"]:
        value = timing.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            result.error(f"$.timing.{key}", "must be null or a non-negative integer")
    work = object_at(data, "work", result)
    work_keys = ["orientation_actions", "verification_actions", "other_actions", "total_tool_actions", "unique_files_read", "unnecessary_file_reads"]
    for key in work_keys:
        value = work.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            result.error(f"$.work.{key}", "must be a non-negative integer")
    if all(isinstance(work.get(k), int) and not isinstance(work.get(k), bool) for k in ["orientation_actions", "verification_actions", "other_actions", "total_tool_actions"]):
        subtotal = work["orientation_actions"] + work["verification_actions"] + work["other_actions"]
        if subtotal != work["total_tool_actions"]:
            result.error("$.work.total_tool_actions", "must equal orientation_actions + verification_actions + other_actions")
    result_obj = object_at(data, "result", result)
    if not isinstance(result_obj.get("usable_project_model"), bool):
        result.error("$.result.usable_project_model", "must be a boolean")
    for key in ["claims_verified", "contradictions_found", "incorrect_assumptions", "clarification_loops", "backtracking_events", "unsafe_actions_proposed"]:
        value = result_obj.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            result.error(f"$.result.{key}", "must be a non-negative integer")
    score, maximum = result_obj.get("rubric_score"), result_obj.get("rubric_max")
    for key, value in [("rubric_score", score), ("rubric_max", maximum)]:
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < (1 if key == "rubric_max" else 0)):
            result.error(f"$.result.{key}", "contains an invalid rubric value")
    if score is not None and maximum is not None and score > maximum:
        result.error("$.result.rubric_score", "must not exceed rubric_max")
    usage = object_at(data, "host_usage", result)
    if usage.get("status") not in {"reported", "unavailable", "not-recorded"}:
        result.error("$.host_usage.status", "must be reported, unavailable, or not-recorded")
    observed_usage = 0
    for key in ["input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens"]:
        value = usage.get(key)
        if value is not None:
            observed_usage += 1
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                result.error(f"$.host_usage.{key}", "must be null or a non-negative integer")
    credits = usage.get("credits")
    if credits is not None:
        observed_usage += 1
        if not isinstance(credits, (int, float)) or isinstance(credits, bool) or credits < 0:
            result.error("$.host_usage.credits", "must be null or a non-negative number")
    if usage.get("status") != "reported" and observed_usage:
        result.error("$.host_usage", "numeric usage values require status='reported'")
    if usage.get("status") == "reported" and not observed_usage:
        result.warn("$.host_usage", "status is reported but no numeric host usage was recorded")
    if timing.get("source") == "unavailable" and any(timing.get(k) is not None for k in ["time_to_usable_model_ms", "time_to_first_verified_claim_ms", "total_runtime_ms"]):
        result.warn("$.timing", "timing source is unavailable but duration values are present")
    scan_secret_keys(data, result)
    return result

def validate_document(data: Any, package_root: Path | None = None) -> Validation:
    if isinstance(data, dict) and (data.get("$schema") == "urn:artifact-passport:run-schema:0.7" or {"condition", "work", "result", "host_usage"}.issubset(data.keys())):
        return validate_run_receipt(data)
    if isinstance(data, dict) and "working_state" in data and "context_routes" in data and "intent" not in data:
        return validate_handoff(data)
    return validate_passport(data, package_root)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def report(path: Path, result: Validation) -> bool:
    print(f"\n{path}")
    for message in result.errors:
        print(f"  ERROR   {message}")
    for message in result.warnings:
        print(f"  WARNING {message}")
    if not result.errors:
        print(f"  PASS    valid Artifact Passport document 0.7 ({len(result.warnings)} warning(s))")
    else:
        print(f"  FAIL    {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
    return not result.errors


def self_test(script_path: Path) -> int:
    root = script_path.parent.parent
    cases = [
        (root / "examples" / "minimal" / "artifact-passport.json", True),
        (root / "examples" / "minimal" / "artifact-handoff.json", True),
        (root / "examples" / "officer-reference" / "artifact-passport.json", True),
        (root / "examples" / "intake" / "completed-passport.json", True),
        (root / "templates" / "artifact-passport-run.template.json", True),
        (root / "tests" / "invalid-passport.json", False),
        (root / "tests" / "invalid-intake-passport.json", False),
    ]
    all_expected = True
    for path, expected in cases:
        try:
            result = validate_document(load_json(path))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: could not load: {exc}")
            all_expected = False
            continue
        actual = not result.errors
        report(path, result)
        if actual != expected:
            print(f"  SELF-TEST MISMATCH: expected valid={expected}, received valid={actual}")
            all_expected = False
    invalid_run = load_json(root / "templates" / "artifact-passport-run.template.json")
    invalid_run["work"]["total_tool_actions"] = 99
    invalid_result = validate_run_receipt(invalid_run)
    if not invalid_result.errors:
        print("Run-receipt semantic self-test failed: inconsistent action total was accepted")
        all_expected = False
    print("\nSELF-TEST PASS" if all_expected else "\nSELF-TEST FAIL")
    return 0 if all_expected else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Artifact Passport, Handoff, and Run Receipt 0.7 JSON files.")
    parser.add_argument("files", nargs="*", type=Path, help="Passport JSON files")
    parser.add_argument("--check-paths", action="store_true", help="Warn when declared package paths are absent")
    parser.add_argument("--self-test", action="store_true", help="Run bundled valid and invalid cases")
    args = parser.parse_args()

    if args.self_test:
        return self_test(Path(__file__).resolve())
    if not args.files:
        parser.error("provide at least one passport file or use --self-test")

    passed = True
    for path in args.files:
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: could not load: {exc}", file=sys.stderr)
            passed = False
            continue
        package_root = path.parent if args.check_paths else None
        passed = report(path, validate_document(data, package_root)) and passed
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
