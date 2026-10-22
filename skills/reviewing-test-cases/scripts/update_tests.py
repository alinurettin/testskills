#!/usr/bin/env python3
"""Review and apply local test-suite changes. No vendor APIs or update-file claims.

  python update_tests.py plan --source qa/test-cases.json --incoming edited.xlsx --out qa/update-plan.json
  python update_tests.py apply --source qa/test-cases.json --plan qa/update-plan.json

plan is read-only for the source. It writes a deterministic manifest of add/update/deprecate,
metadata changes and conflicts. QA Suite XLSX includes its baseline, enabling conservative
three-way conflict checks. JSON is treated as an explicit full desired suite; omitted tests
are deprecated, never deleted. The manifest is not a vendor-import update format.

apply requires the reviewed manifest and unchanged source-byte SHA256, validates its integrity,
uses an exclusive advisory lock, stages the result beside the source, then atomically replaces
it. The lock coordinates this tool, not unrelated editors; a final hash check detects edits
before replacement but cannot provide a transaction with non-cooperating external writers.
Exit: 0 success, 1 plan contains conflicts, 2 invalid input/stale source/apply failure.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


_spec = importlib.util.spec_from_file_location("qa_update_import", Path(__file__).with_name("import_tests.py"))
_importer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_importer)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _read(path):
    raw = Path(path).read_bytes()
    document = json.loads(raw.decode("utf-8-sig"))
    _importer.validate_document(document)
    return raw, document


def _index(document):
    return {test["id"]: test for test in document["test_cases"]}


def plan_updates(source: Path, incoming: Path):
    """Build a deterministic, reviewable local delta. Does not write the source."""
    raw, current = _read(source)
    if _importer.is_xlsx(Path(incoming)):
        imported = _importer.import_roundtrip(Path(incoming))
        baseline, desired = imported["baseline"], imported["document"]
    else:
        candidate_raw, desired = _read(incoming)
        sidecar = Path(incoming).with_name(Path(incoming).name + ".qa-baseline.json")
        if sidecar.exists():
            provenance = json.loads(sidecar.read_text(encoding="utf-8-sig"))
            if type(provenance.get("metadata_version")) is not int or provenance["metadata_version"] != 1:
                raise ValueError("unsupported baseline metadata version")
            if provenance.get("candidate_sha256") != digest(candidate_raw):
                raise ValueError("candidate changed since workbook import; re-import it to refresh baseline provenance")
            baseline = _importer.validate_document(provenance.get("baseline"))
        else:
            baseline = copy.deepcopy(current)
    if baseline.get("project") and current.get("project") and baseline["project"] != current["project"]:
        raise ValueError("incoming baseline belongs to a different project; re-export from the intended source")
    old, now, wanted = _index(baseline), _index(current), _index(desired)
    target = copy.deepcopy(current)
    target_tests = _index(target)
    actions, conflicts = [], []
    # Baseline controls the XLSX scope: unexported tests are never implicitly retired.
    for tid in sorted(set(old) | set(wanted)):
        before, base, after = now.get(tid), old.get(tid), wanted.get(tid)
        if after is None:
            if before is None or before.get("status") == "deprecated":
                continue
            after = copy.deepcopy(base)
            after["status"] = "deprecated"
        if after == base or after == before:
            continue
        if before != base:
            conflicts.append({"id": tid, "base": base, "current": before, "incoming": after,
                              "reason": "source and incoming both changed this test"})
            continue
        operation = "add" if before is None else "deprecate" if after.get("status") == "deprecated" \
            and before.get("status") != "deprecated" else "update"
        actions.append({"id": tid, "operation": operation, "before": before, "after": after})
        target_tests[tid] = copy.deepcopy(after)
    # Preserve current ordering; new IDs append in deterministic order.
    ordered = [t["id"] for t in current["test_cases"]]
    ordered += sorted(set(target_tests) - set(ordered))
    target["test_cases"] = [target_tests[tid] for tid in ordered]
    for key in sorted(set(desired) - {"test_cases"}):
        before, base, after = current.get(key), baseline.get(key), desired[key]
        if after == base or after == before:
            continue
        if before != base:
            conflicts.append({"id": "$document." + key, "base": base, "current": before,
                              "incoming": after, "reason": "document metadata changed on both sides"})
            continue
        target[key] = copy.deepcopy(after)
        actions.append({"id": "$document." + key, "operation": "metadata", "before": before, "after": after})
    _importer.validate_document(target)
    plan = {"plan_version": 1, "source_sha256": digest(raw), "target_sha256": digest(canonical(target)),
            "actions": actions, "conflicts": conflicts, "target_document": target,
            "scope": "local suite delta only; no vendor update/import has been performed"}
    plan["plan_id"] = digest(canonical(plan))
    return plan


def apply_plan(source: Path, plan: dict):
    """Apply a reviewed plan only to the exact source snapshot; atomic local replacement."""
    source = Path(source)
    if source.is_symlink():
        raise ValueError("apply to a regular source file, not a symbolic link")
    if type(plan.get("plan_version")) is not int or plan["plan_version"] != 1:
        raise ValueError("unsupported plan_version")
    unsigned = {k: v for k, v in plan.items() if k != "plan_id"}
    if plan.get("plan_id") != digest(canonical(unsigned)):
        raise ValueError("plan integrity check failed; regenerate and review the plan")
    if plan.get("conflicts"):
        raise ValueError("plan contains conflicts; resolve and regenerate it before apply")
    target = _importer.validate_document(plan.get("target_document"))
    if digest(canonical(target)) != plan.get("target_sha256"):
        raise ValueError("target integrity check failed")
    lock = source.with_name("." + source.name + ".qa-update.lock")
    marker = source.with_name(source.name + ".qa-reviewed.json")
    created = False
    staged = None
    marker_stage = None
    marker_written = False
    source_replaced = False
    previous_marker = None
    try:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as e:
            raise ValueError("source is locked by another update; inspect a stale lock before removing it") from e
        created = True
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(str(os.getpid()) + "\n")
        raw, current = _read(source)
        if digest(raw) != plan["source_sha256"]:
            raise ValueError("source changed since planning (stale source hash); regenerate the plan")
        if not plan["actions"]:
            return {"applied": 0, "source_sha256": digest(raw)}
        mode = stat.S_IMODE(source.stat().st_mode)
        fd, name = tempfile.mkstemp(prefix="." + source.name + ".", suffix=".tmp", dir=source.parent)
        staged = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(target, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(staged, mode)
        # Guard the old compact source before replacing JSON. A crash in between is conservative:
        # qa_compact will stop rather than overwrite a reviewed suite from stale source text.
        previous_marker = marker.read_bytes() if marker.exists() else None
        guard = {"schema_version": 1, "source_sha256": digest(staged.read_bytes()),
                 "explanation": "Reviewed JSON update: compact source may be stale. Compare changes before explicit replacement."}
        fd, name = tempfile.mkstemp(prefix="." + marker.name + ".", suffix=".tmp", dir=source.parent)
        marker_stage = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(guard, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(marker_stage, marker)
        marker_stage = None
        marker_written = True
        if digest(source.read_bytes()) != plan["source_sha256"]:
            raise ValueError("source changed while preparing update; nothing applied")
        os.replace(staged, source)
        source_replaced = True
        staged = None
        return {"applied": len(plan["actions"]), "source_sha256": digest(source.read_bytes())}
    finally:
        try:
            if marker_stage is not None:
                marker_stage.unlink(missing_ok=True)
            if marker_written and not source_replaced:
                if previous_marker is None:
                    marker.unlink(missing_ok=True)
                else:
                    # Restore the previous guard atomically if source replacement failed.
                    fd, name = tempfile.mkstemp(prefix="." + marker.name + ".", suffix=".tmp", dir=source.parent)
                    rollback = Path(name)
                    try:
                        with os.fdopen(fd, "wb") as handle:
                            handle.write(previous_marker)
                            handle.flush()
                            os.fsync(handle.fileno())
                        os.replace(rollback, marker)
                    finally:
                        rollback.unlink(missing_ok=True)
        finally:
            try:
                if staged is not None:
                    staged.unlink(missing_ok=True)
            finally:
                if created:
                    lock.unlink(missing_ok=True)


def migrate_document(document):
    """Explicit, lossless legacy-to-v1 migration; business version is unchanged."""
    _importer.validate_document(document)
    migrated = copy.deepcopy(document)
    migrated["schema_version"] = 1
    return migrated


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="dry run: write a deterministic change manifest")
    plan_cmd.add_argument("--source", required=True)
    plan_cmd.add_argument("--incoming", required=True, help="QA Suite XLSX or full desired JSON document")
    plan_cmd.add_argument("--out", required=True)
    apply_cmd = sub.add_parser("apply", help="explicitly apply a reviewed plan")
    apply_cmd.add_argument("--source", required=True)
    apply_cmd.add_argument("--plan", required=True)
    migrate_cmd = sub.add_parser("migrate", help="write a schema_version=1 candidate; source remains unchanged")
    migrate_cmd.add_argument("--source", required=True)
    migrate_cmd.add_argument("--out", required=True)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = ap.parse_args()
    try:
        if args.command == "migrate":
            destination = Path(args.out)
            if destination.resolve() == Path(args.source).resolve():
                raise ValueError("migration output must differ from source; review and apply it through a plan")
            _, document = _read(args.source)
            candidate = migrate_document(document)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8", newline="\n")
            print(f"wrote {destination}: schema version 1 candidate; source unchanged")
            return 0
        if args.command == "plan":
            destination = Path(args.out)
            if destination.resolve() in (Path(args.source).resolve(), Path(args.incoming).resolve()):
                raise ValueError("plan output must differ from source and incoming")
            plan = plan_updates(Path(args.source), Path(args.incoming))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            print(f"wrote {destination}: {len(plan['actions'])} actions, {len(plan['conflicts'])} conflicts; source unchanged")
            return 1 if plan["conflicts"] else 0
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
        result = apply_plan(Path(args.source), plan)
        print(f"applied {result['applied']} local actions; no vendor import performed")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
