#!/usr/bin/env python3
"""Prepare allowlisted evaluation workspaces, record provenance, summarise scores.

No model/service calls. Filesystem isolation must be enforced by the runner;
copying a workspace is not an access-control boundary. Historical records are
read-only inputs. See docs/EVALUATION-HARNESS.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = {"baseline", "checklist", "scripts", "full"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def within(path, parent):
    return path == parent or parent in path.parents


def versioned(value):
    if (not isinstance(value, dict) or type(value.get("schema_version", 1)) is not int
            or value.get("schema_version", 1) != 1):
        raise ValueError("expected a schema_version 1 object")
    return value


def checked_relative(value):
    if not isinstance(value, str):
        raise ValueError("expected a relative POSIX path string")
    path = Path(value)
    reserved = {"con", "prn", "aux", "nul"} | {f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10)}
    if (not value or not path.parts or path.is_absolute() or ".." in path.parts or ":" in value
            or "\\" in value or "\x00" in value or any(c in value for c in '*?"<>|')
            or any(part.endswith((" ", ".")) or part.split(".", 1)[0].casefold() in reserved for part in path.parts)):
        raise ValueError(f"expected a relative POSIX path: {value}")
    return path


def json_key(value):
    """Validate finite JSON metadata and use a canonical comparison key."""
    try:
        return json.dumps(value, sort_keys=True, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"metadata must contain finite JSON values: {exc}")


def string_list(value, name):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{name} must be a list of nonempty strings")
    return value


def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def validate_observation(value, *, artifact_records=False):
    versioned(value)
    json_key(value)
    if "contaminated" in value and not isinstance(value["contaminated"], bool):
        raise ValueError("contaminated must be true or false")
    for name in ("contamination_reasons", "missed", "artifacts"):
        if name in value and not (name == "missed" and value[name] is None):
            # Recorded artifacts have hashes; input observations use path strings.
            if (artifact_records and name == "artifacts" and isinstance(value[name], list)
                    and all(isinstance(v, dict) for v in value[name])):
                continue
            string_list(value[name], name)
    for name in ("duration_seconds", "tokens", "tool_calls", "cost", "found", "total", "false_positives"):
        number = value.get(name)
        if number is not None:
            finite_number(number, name)
            if name in {"tokens", "tool_calls", "false_positives"} and type(number) is not int:
                raise ValueError(f"{name} must be an integer")
    if value.get("found") is not None and value.get("total") is not None and value["found"] > value["total"]:
        raise ValueError("found exceeds total")
    grader = value.get("grader")
    if grader is not None and (not isinstance(grader, (str, dict)) or not grader):
        raise ValueError("grader must be a nonempty model ID or metadata object")


def prepare(config, destination, repo=ROOT):
    config = versioned(config)
    json_key(config)
    for key in ("run_id", "trial", "model"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f"{key} must be a nonempty string (use an exact model ID)")
    if config.get("arm") not in ARMS:
        raise ValueError(f"arm must be one of {sorted(ARMS)}")
    if not isinstance(config.get("inputs"), list) or not config["inputs"]:
        raise ValueError("inputs must explicitly allowlist at least one file")
    repo, dest = Path(repo).resolve(), Path(destination).resolve()
    manifest_path = dest.with_name(dest.name + ".manifest.json")
    if within(dest, repo) or dest.exists() or manifest_path.exists():
        raise ValueError("use a new workspace outside the repository, with no existing manifest")
    planned, targets = [], set()
    for item in config["inputs"]:
        if not isinstance(item, dict):
            raise ValueError("each input must contain source and path strings")
        relative = checked_relative(item["source"])
        target = checked_relative(item["path"])
        source = repo / relative
        forbidden = {"keys", "tests", "examples", "results", "workspace", "demo-app", "app"}
        resolved = source.resolve()
        if (not within(resolved, repo) or source.is_symlink() or not source.is_file()
                or forbidden.intersection(p.casefold() for p in relative.parts)
                or forbidden.intersection(p.casefold() for p in resolved.relative_to(repo).parts)
                or source.name.casefold() in {"run.md", "server.js", "server.mjs"}):
            raise ValueError(f"unsafe/non-input source: {relative}")
        target_key = target.as_posix().casefold()
        if (target.parts[0].casefold() in {"context", "tools", "skills"}
                or any(target_key == p or target_key.startswith(p + "/") or p.startswith(target_key + "/")
                       for p in targets)):
            raise ValueError(f"duplicate/reserved input target: {target}")
        targets.add(target_key)
        planned.append((source, target, digest(source)))
    selected = config.get("skills", [])
    string_list(selected, "skills")
    if config["arm"] in {"scripts", "full"}:
        if not selected or len(selected) != len(set(selected)):
            raise ValueError("scripts/full arms require a unique explicit skills list")
        for name in selected:
            if (checked_relative(name).parts != (name,) or not (repo / "skills" / name / "SKILL.md").is_file()
                    or linked(repo / "skills") or linked(repo / "skills" / name)):
                raise ValueError(f"unknown skill: {name}")
            skill_root = repo / "skills" / name
            if not within(skill_root.resolve(), repo):
                raise ValueError(f"skill is outside repository: {name}")
            for path in skill_root.rglob("*"):
                if linked(path) or not within(path.resolve(), skill_root.resolve()):
                    raise ValueError(f"skill contains a linked/escaping path: {name}/{path.relative_to(skill_root)}")
    if selected and config["arm"] not in {"scripts", "full"}:
        raise ValueError("baseline/checklist arms must not select skills")
    if config["arm"] == "checklist" and (not isinstance(config.get("checklist"), str) or not config["checklist"].strip()):
        raise ValueError("checklist arm requires checklist text")
    dest.mkdir(parents=True)
    inventory = []
    for source, target, expected in planned:
        out = dest / target
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, out)
        if digest(out) != expected:
            raise ValueError("input changed while preparing the workspace")
        inventory.append({"path": target.as_posix(), "sha256": expected})
    if config["arm"] == "checklist":
        (dest / "context").mkdir()
        (dest / "context/checklist.md").write_text(config["checklist"], encoding="utf-8", newline="\n")
    for name in selected if config["arm"] in {"scripts", "full"} else []:
        source = repo / "skills" / name
        if config["arm"] == "full":
            shutil.copytree(source, dest / "skills" / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            for folder in ("scripts", "assets"):
                if (source / folder).exists():
                    shutil.copytree(source / folder, dest / "tools" / name / folder,
                                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for folder in ("context", "skills", "tools"):
        for path in sorted((dest / folder).rglob("*")):
            if path.is_file():
                inventory.append({"path": path.relative_to(dest).as_posix(), "sha256": digest(path)})
    git = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True)
    plugin = repo / ".claude-plugin/plugin.json"
    manifest = {**config, "schema_version": 1, "workspace": str(dest),
                "prepared_at": datetime.now(timezone.utc).isoformat(),
                "repository_commit": git.stdout.strip() if git.returncode == 0 else None,
                "repository_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
                "suite_version": read(plugin).get("version") if plugin.is_file() else None,
                "inventory": inventory, "isolation": "runner-enforcement-required"}
    write_new(manifest_path, manifest)
    return manifest_path


def finite_number(value, name, *, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be a finite number >= {minimum}")
    return value


def record(manifest_path, observation, output):
    manifest = versioned(read(manifest_path))
    validate_observation(observation)
    for name in ("run_id", "trial", "model", "workspace"):
        if not isinstance(manifest.get(name), str) or not manifest[name].strip():
            raise ValueError(f"manifest {name} must be a nonempty string")
    if manifest.get("arm") not in ARMS:
        raise ValueError("manifest arm is invalid")
    if not isinstance(manifest.get("inventory"), list) or not manifest["inventory"]:
        raise ValueError("manifest inventory must be a nonempty list")
    score = finite_number(observation.get("score"), "score")
    maximum = finite_number(observation.get("max"), "max", minimum=1e-100)
    if score > maximum:
        raise ValueError("score exceeds max")
    metrics = {key: observation.get(key) for key in ("duration_seconds", "tokens", "tool_calls", "cost")}
    for key, value in metrics.items():
        if value is not None:
            finite_number(value, key)
    workspace = Path(manifest["workspace"]).resolve()
    if not Path(manifest["workspace"]).is_absolute() or not workspace.is_dir():
        raise ValueError("manifest workspace must be an existing absolute directory")
    if within(Path(manifest_path).resolve(), workspace) or within(Path(output).resolve(), workspace):
        raise ValueError("evaluator manifests/results must be outside the agent workspace")
    reasons = list(observation.get("contamination_reasons", []))
    for item in manifest["inventory"]:
        if (not isinstance(item, dict) or not isinstance(item.get("sha256"), str)
                or len(item["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in item["sha256"])):
            raise ValueError("manifest inventory entries require path and SHA-256")
        path = workspace / checked_relative(item["path"])
        if not path.is_file() or not within(path.resolve(), workspace) or digest(path) != item["sha256"]:
            reasons.append("input/context changed: " + item["path"])
    artifacts = []
    for relative in observation.get("artifacts", []):
        path = workspace / checked_relative(relative)
        if not within(path.resolve(), workspace) or not path.is_file():
            raise ValueError(f"artifact is missing or outside workspace: {relative}")
        artifacts.append({"path": relative, "sha256": digest(path)})
    result = {**manifest, **{k: observation.get(k) for k in ("score", "max", "found", "total", "false_positives", "missed", "grader")},
              **metrics, "artifacts": artifacts, "contaminated": bool(reasons) or bool(observation.get("contaminated")),
              "contamination_reasons": reasons, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": digest(manifest_path)}
    write_new(output, result)
    return result


def distribution(values):
    return {"n": len(values), "mean": statistics.mean(values), "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else None,
            "min": min(values), "max": max(values), "ceiling_count": sum(v == 100 for v in values)}


def summarize(documents):
    groups, seen, excluded = defaultdict(list), set(), []
    for document in documents:
        versioned(document)
        runs = document.get("runs", [document])
        if not isinstance(runs, list):
            raise ValueError("runs must be a list")
        for run in runs:
            validate_observation(run, artifact_records=True)
            identity = run.get("run_id", run.get("id"))
            if not isinstance(identity, str) or not identity.strip() or identity in seen:
                raise ValueError("every run needs a unique run_id/id")
            seen.add(identity)
            if run.get("contaminated") or run.get("contamination_reasons"):
                excluded.append(identity)
                continue
            score = finite_number(run["score"], "score")
            maximum = finite_number(run["max"], "max", minimum=1e-100)
            if score > maximum:
                raise ValueError("score exceeds max")
            for name in ("model", "arm", "trial"):
                if not isinstance(run.get(name), str) or not run[name].strip():
                    raise ValueError(f"run {name} must be a nonempty string")
            if run["arm"] not in ARMS | {"skill", "noskill"}:
                raise ValueError("run arm is invalid")
            cohort = json_key({"parameters": run.get("parameters"), "grader": run.get("grader"),
                               "repository_commit": run.get("repository_commit")})
            key = (run["model"], run["arm"], run["trial"], cohort)
            groups[key].append((100 * score / maximum, run))
    rows, task_means = [], defaultdict(dict)
    for (model, arm, trial, cohort), group in sorted(groups.items()):
        row = {"model": model, "arm": arm, "trial": trial, **json.loads(cohort),
               **distribution([v for v, _ in group])}
        row["missing_metadata"] = {k: sum(r.get(k) is None for _, r in group)
                                   for k in ("duration_seconds", "tokens", "tool_calls", "cost", "grader")}
        rows.append(row)
        task_means[(model, arm, cohort)][trial] = row["mean"]
    comparisons = []
    for (model, arm, cohort), means in sorted(task_means.items()):
        baseline = "noskill" if arm == "skill" else "baseline"
        if arm in {"baseline", "noskill"}:
            continue
        base = task_means.get((model, baseline, cohort), {})
        matched = sorted(set(means) & set(base))
        if not matched:
            continue
        deltas = [means[t] - base[t] for t in matched]
        interval = None
        if len(deltas) >= 5:
            rng = random.Random(42)
            draws = sorted(statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(2000))
            interval = [draws[49], draws[1949]]
        comparisons.append({"model": model, "arm": arm, "baseline": baseline, **json.loads(cohort),
                            "independent_tasks": len(matched), "mean_task_delta": statistics.mean(deltas),
                            "bootstrap_95_task_interval": interval})
    return {"schema_version": 1, "groups": rows, "comparisons": comparisons, "excluded_contaminated": excluded,
            "note": "Scores are descriptive. Bootstrap resamples matched tasks, not repeated runs. "
                    "Intervals require >=5 tasks; task independence and grader validity are not verified."}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("config"); p.add_argument("--dest", required=True)
    p = sub.add_parser("record")
    p.add_argument("manifest"); p.add_argument("observation"); p.add_argument("--out", required=True)
    p = sub.add_parser("report")
    p.add_argument("inputs", nargs="+"); p.add_argument("--out")
    args = ap.parse_args()
    try:
        if args.command == "prepare":
            print(prepare(read(args.config), args.dest))
        elif args.command == "record":
            record(args.manifest, read(args.observation), args.out)
            print(args.out)
        else:
            result = summarize([read(p) for p in args.inputs])
            if args.out:
                write_new(args.out, result)
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
