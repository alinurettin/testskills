#!/usr/bin/env python3
"""Compact authoring format <-> QA Suite JSON (requirements.json / test-cases.json).

Writing JSON by hand is slow, token-hungry and error-prone (a test case is
~1.8 KB of JSON). Author in this compact text format instead and let the
script produce validated JSON. The compact file (e.g. qa/test-cases.src.md)
is the editable source; the JSON is the generated artifact other scripts read.

Test cases (kind "tc"):
    project: Online Mağaza – Kupon          # optional header lines
    language: tr
    setup login: Kullanıcı 'ayse.test@example.com' ile giriş yapmış   # shared precondition block,
    setup login: Sepet boş                                            # referenced as "pre: @login"

    ## TC-001 | Kupon 100,00 TL sınırında uygulanır
    req: REQ-001 | pri: h | pol: + | tech: bva | ref: DS-001 C-02 | cat: functional | ext: SHOP-201
    obj: Tam sınır değerinde indirim uygulanır        # optional, keep it short
    pre: Kullanıcı giriş yapmış                        # one line per precondition
    pre: 'YAZ10' kuponu aktif
    data: sepet=100,00 TL; kupon=YAZ10                 # key=value pairs separated by ';'
    1. Sepete 100,00 TL tutarında ürün ekle [Ürün A x1] => Sepet toplamı 100,00 TL
    2. Kupon alanına kodu yaz, 'Uygula'ya tıkla [YAZ10] => 'Kupon uygulandı'; toplam 90,00 TL
    post: Kupon kullanım kaydı silinir                 # optional
    tags: smoke, regression | auto: yes, veri güdümlü | status: ready

  Step syntax: "N. action [data] => expected". The optional [data] is the LAST
  bracket group before "=>"; quote UI labels with '...' instead of brackets.
  Data whose whitespace matters goes in JSON quotes: [" YAZ10 "].
  "pre: @name" expands to every line of "setup name: ..." (the JSON stays complete
  for exports); write shared setup once instead of repeating it in every test.

Requirements (kind "req"):
    ## REQ-001 | Kupon ile %10 indirim
    type: business-rule | pri: h | risk: 3x4 Gelir etkisi | src: US-42 AK-1 | ext: SHOP-42 | status: ready
    text: Kayıtlı müşteri, sepet tutarı 100 TL ve üzerindeyse geçerli kupon ile %10 indirim almalıdır.
    ac: Diyelim ki sepet 150 TL, Eğer ki YAZ10 uygulanırsa, O zaman toplam 135 TL olur
    q: Q-001, Q-004 | derived: no | nfr: performance-efficiency | parent: REQ-000
    notes: ...

Aliases: pri c/h/m/l; pol +/-; tech ep, bva, dt, st, pw, ct, uc, sc, crud, eg, cl, ex, rb;
status (req) draft/cn/ready/deferred/deprecated.

Usage:
  python qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json [--merge]
  python qa_compact.py req qa/requirements.src.md --out qa/requirements.json [--merge]
  python qa_compact.py tc qa/test-cases.json --to-compact --out qa/test-cases.src.md   # reverse
--merge keeps entries of an existing --out file that the source does not mention
(IDs are never renumbered). Exit 0 ok, 1 validation errors (nothing written), 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PRI = {"c": "critical", "h": "high", "m": "medium", "l": "low",
       "critical": "critical", "high": "high", "medium": "medium", "low": "low"}
POL = {"+": "positive", "-": "negative", "−": "negative", "positive": "positive", "negative": "negative",
       "pos": "positive", "neg": "negative"}
TECH = {"ep": "equivalence-partitioning", "bva": "boundary-value-analysis", "dt": "decision-table",
        "st": "state-transition", "pw": "pairwise", "ct": "classification-tree", "uc": "use-case",
        "sc": "scenario", "crud": "crud", "eg": "error-guessing", "cl": "checklist", "ex": "exploratory",
        "rb": "requirements-based"}
TECH_FULL = set(TECH.values())
REQ_STATUS = {"cn": "clarification-needed", "draft": "draft", "ready": "ready", "deferred": "deferred",
              "deprecated": "deprecated", "clarification-needed": "clarification-needed"}
REQ_TYPES = {"functional", "non-functional", "business-rule", "interface", "data", "constraint", "compliance"}
HEAD = re.compile(r"^##\s+((?:TC|REQ)-\d{3,})\s*\|\s*(.+?)\s*$")
STEP = re.compile(r"^(\d+)[.)]\s+(.*?)\s+=>\s*(.*)$")
FIELD = re.compile(r"^([a-zA-Z_]+)\s*:\s*(.*)$")
TC_ORDER = ["id", "external_id", "title", "objective", "requirement_ids", "priority", "polarity", "category", "technique",
            "design_ref", "preconditions", "test_data", "steps", "postconditions", "tags", "automation", "status"]


def split_pipes(line: str) -> list[tuple[str, str]]:
    """'a: 1 | b: 2' -> [('a','1'),('b','2')]; a segment without 'key:' continues the previous value."""
    out: list[tuple[str, str]] = []
    for seg in line.split(" | "):
        m = FIELD.match(seg.strip())
        if m:
            out.append((m.group(1).lower(), m.group(2).strip()))
        elif out:
            out[-1] = (out[-1][0], out[-1][1] + " | " + seg.strip())
    return out


def csv_list(v: str) -> list[str]:
    return [x.strip() for x in v.split(",") if x.strip()]


def parse(text: str, kind: str):
    header: dict = {}
    items: list[dict] = []
    errors: list[str] = []
    cur = None
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("<!--"):
            continue
        h = HEAD.match(line)
        if h:
            prefix = "TC" if kind == "tc" else "REQ"
            if not h.group(1).startswith(prefix):
                errors.append(f"line {no}: expected a {prefix}-### heading, got {h.group(1)}")
            cur = {"id": h.group(1), "title": h.group(2), "_line": no}
            items.append(cur)
            continue
        if cur is None:
            m = FIELD.match(line.strip())
            sm = re.match(r"^setup\s+([\w-]+)\s*:\s*(.+)$", line.strip())
            if sm:
                header.setdefault("_setup", {}).setdefault(sm.group(1), []).append(sm.group(2).strip())
            elif m and m.group(1).lower() in ("project", "language", "version"):
                header[m.group(1).lower()] = m.group(2).strip()
            elif not line.startswith("#"):
                errors.append(f"line {no}: text outside of an item: {line[:60]}")
            continue
        s = STEP.match(line.strip())
        if s and kind == "tc":
            action, expected = s.group(2).strip(), s.group(3).strip()
            data = ""
            dm = re.match(r"^(.*)\s\[([^\[\]]*)\]\s*$", action)
            if dm:
                action, data = dm.group(1).strip(), dm.group(2).strip()
                if len(data) >= 2 and data[0] == data[-1] == '"':
                    try:
                        data = json.loads(data)
                    except ValueError:
                        pass
            step = {"action": action, "expected": expected}
            if data:
                step["data"] = data
            cur.setdefault("steps", []).append(step)
            continue
        fields = split_pipes(line.strip())
        if not fields:
            errors.append(f"line {no} ({cur['id']}): cannot parse: {line[:60]}")
            continue
        for key, val in fields:
            if key == "pre" and val.startswith("@"):
                block = header.get("_setup", {}).get(val[1:].strip())
                if block is None:
                    errors.append(f"line {no} ({cur['id']}): unknown setup block '{val}'")
                    continue
                cur.setdefault("preconditions", []).extend(block)
                continue
            err = apply_field(cur, kind, key, val)
            if err:
                errors.append(f"line {no} ({cur['id']}): {err}")
    return header, items, errors


def apply_field(cur: dict, kind: str, key: str, val: str) -> str | None:
    if kind == "tc":
        if key == "req":
            cur["requirement_ids"] = csv_list(val)
        elif key == "pri":
            if val.lower() not in PRI:
                return f"unknown priority '{val}'"
            cur["priority"] = PRI[val.lower()]
        elif key == "pol":
            if val.lower() not in POL:
                return f"unknown polarity '{val}'"
            cur["polarity"] = POL[val.lower()]
        elif key == "tech":
            t = TECH.get(val.lower(), val.lower())
            if t not in TECH_FULL:
                return f"unknown technique '{val}'"
            cur["technique"] = t
        elif key == "ref":
            cur["design_ref"] = val
        elif key == "cat":
            cur["category"] = val
        elif key == "obj":
            cur["objective"] = val
        elif key == "pre":
            cur.setdefault("preconditions", []).append(val)
        elif key == "post":
            cur.setdefault("postconditions", []).append(val)
        elif key == "data":
            d = {}
            for pair in val.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    d[k.strip()] = v.strip()
                elif pair.strip():
                    d[f"note{len(d) + 1}"] = pair.strip()
            cur["test_data"] = d
        elif key == "tags":
            cur["tags"] = csv_list(val)
        elif key == "auto":
            flag, _, reason = val.partition(",")
            cur["automation"] = {"candidate": flag.strip().lower() in ("yes", "y", "evet", "true", "1"),
                                 "reason": reason.strip()}
        elif key == "status":
            cur["status"] = val.lower()
        elif key == "ext":
            cur["external_id"] = val
        else:
            return f"unknown field '{key}'"
    else:
        if key == "type":
            if val not in REQ_TYPES:
                return f"unknown type '{val}'"
            cur["type"] = val
        elif key == "pri":
            if val.lower() not in PRI:
                return f"unknown priority '{val}'"
            cur["priority"] = PRI[val.lower()]
        elif key == "risk":
            m = re.match(r"^(\d)\s*[x×*]\s*(\d)\s*(.*)$", val)
            if not m:
                return f"risk must look like '3x4 rationale', got '{val}'"
            cur["risk"] = {"likelihood": int(m.group(1)), "impact": int(m.group(2)), "rationale": m.group(3).strip()}
        elif key == "src":
            cur["source"] = val
        elif key == "ext":
            cur["external_id"] = val
        elif key == "status":
            if val.lower() not in REQ_STATUS:
                return f"unknown status '{val}'"
            cur["status"] = REQ_STATUS[val.lower()]
        elif key == "text":
            cur["text"] = val
        elif key == "ac":
            cur.setdefault("acceptance_criteria", []).append(val)
        elif key == "q":
            cur["questions"] = csv_list(val)
        elif key == "derived":
            cur["derived"] = val.lower() in ("yes", "y", "evet", "true", "1")
        elif key == "nfr":
            cur["quality_characteristic"] = val
        elif key == "parent":
            cur["parent"] = val
        elif key == "notes":
            cur["notes"] = val
        else:
            return f"unknown field '{key}'"
    return None


def validate(items: list[dict], kind: str) -> list[str]:
    errs, seen = [], set()
    for it in items:
        where = f"{it['id']} (line {it.get('_line', '?')})"
        if it["id"] in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(it["id"])
        if kind == "tc":
            for f in ("requirement_ids", "priority", "polarity", "technique"):
                if not it.get(f) and not (f == "requirement_ids" and "exploratory" in it.get("tags", [])):
                    errs.append(f"{where}: missing '{f}'")
            if not it.get("steps"):
                errs.append(f"{where}: no steps ('N. action [data] => expected')")
            nums = [s for s in it.get("steps", []) if not s["expected"] and it.get("technique") != "exploratory"]
            if nums:
                errs.append(f"{where}: step without expected result")
        else:
            for f in ("text", "type", "priority", "source"):
                if not it.get(f):
                    errs.append(f"{where}: missing '{f}'")
            it.setdefault("status", "draft")
            it.setdefault("derived", False)
    return errs


def clean(it: dict, kind: str) -> dict:
    it = {k: v for k, v in it.items() if not k.startswith("_")}
    if kind == "tc":
        it.setdefault("status", "draft")
        return {k: it[k] for k in TC_ORDER if k in it} | {k: v for k, v in it.items() if k not in TC_ORDER}
    return it


def to_compact(data: dict, kind: str) -> str:
    rev_pri = {"critical": "c", "high": "h", "medium": "m", "low": "l"}
    rev_tech = {v: k for k, v in TECH.items()}
    out = []
    for k in ("project", "language", "version"):
        if data.get(k) not in (None, ""):
            out.append(f"{k}: {data[k]}")
    items = data.get("test_cases" if kind == "tc" else "requirements", [])
    for it in items:
        out += ["", f"## {it['id']} | {it.get('title', '')}"]
        if kind == "tc":
            meta = [f"req: {', '.join(it.get('requirement_ids', []))}", f"pri: {rev_pri.get(it.get('priority'), '')}",
                    f"pol: {'+' if it.get('polarity') == 'positive' else '-'}",
                    f"tech: {rev_tech.get(it.get('technique'), it.get('technique', ''))}"]
            if it.get("design_ref"):
                meta.append(f"ref: {it['design_ref']}")
            if it.get("category"):
                meta.append(f"cat: {it['category']}")
            if it.get("external_id"):
                meta.append(f"ext: {it['external_id']}")
            out.append(" | ".join(meta))
            if it.get("objective"):
                out.append(f"obj: {it['objective']}")
            for p in it.get("preconditions", []) if isinstance(it.get("preconditions"), list) else [it["preconditions"]] if it.get("preconditions") else []:
                out.append(f"pre: {p}")
            td = it.get("test_data")
            if isinstance(td, dict) and td:
                out.append("data: " + "; ".join(f"{k}={v}" for k, v in td.items()))
            elif td:
                out.append(f"data: {td}")
            for i, s in enumerate(it.get("steps", []), 1):
                dv = s.get("data") or ""
                if dv and (dv != dv.strip() or any(c in dv for c in "[]") or (dv[0] == dv[-1] == '"')):
                    dv = json.dumps(dv, ensure_ascii=False)
                d = f" [{dv}]" if dv else ""
                out.append(f"{i}. {s.get('action', '')}{d} => {s.get('expected', '')}")
            for p in it.get("postconditions", []) or []:
                out.append(f"post: {p}")
            tail = []
            if it.get("tags"):
                tail.append(f"tags: {', '.join(it['tags'])}")
            if it.get("automation"):
                a = it["automation"]
                tail.append(f"auto: {'yes' if a.get('candidate') else 'no'}" + (f", {a['reason']}" if a.get("reason") else ""))
            tail.append(f"status: {it.get('status', 'draft')}")
            out.append(" | ".join(tail))
        else:
            rk = it.get("risk") or {}
            meta = [f"type: {it.get('type', '')}", f"pri: {rev_pri.get(it.get('priority'), '')}"]
            if rk:
                meta.append(f"risk: {rk.get('likelihood')}x{rk.get('impact')} {rk.get('rationale', '')}".rstrip())
            meta += [f"src: {it.get('source', '')}"]
            if it.get("external_id"):
                meta.append(f"ext: {it['external_id']}")
            meta.append(f"status: {it.get('status', 'draft')}")
            out.append(" | ".join(meta))
            out.append(f"text: {it.get('text', '')}")
            for ac in it.get("acceptance_criteria", []):
                out.append(f"ac: {ac}")
            extra = []
            if it.get("questions"):
                extra.append(f"q: {', '.join(it['questions'])}")
            extra.append(f"derived: {'yes' if it.get('derived') else 'no'}")
            if it.get("quality_characteristic"):
                extra.append(f"nfr: {it['quality_characteristic']}")
            if it.get("parent"):
                extra.append(f"parent: {it['parent']}")
            out.append(" | ".join(extra))
            if it.get("notes"):
                out.append(f"notes: {it['notes']}")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["tc", "req"])
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--merge", action="store_true", help="keep items of an existing --out file not in the source")
    ap.add_argument("--to-compact", action="store_true", help="convert JSON -> compact text instead")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        raw = Path(a.source).read_text(encoding="utf-8-sig")
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.to_compact:
        out.write_text(to_compact(json.loads(raw), a.kind), encoding="utf-8")
        print(f"wrote {out}")
        return 0
    header, items, errors = parse(raw, a.kind)
    errors += validate(items, a.kind)
    if errors:
        print("validation failed, nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    key = "test_cases" if a.kind == "tc" else "requirements"
    doc: dict = {}
    if a.merge and out.exists():
        doc = json.loads(out.read_text(encoding="utf-8-sig"))
    for k in ("project", "language"):
        if header.get(k):
            doc[k] = header[k]
    if a.kind == "req":
        doc["version"] = int(header.get("version") or doc.get("version") or 1)
    new = {it["id"]: clean(it, a.kind) for it in items}
    merged = []
    for old in doc.get(key, []):
        merged.append(new.pop(old["id"], old))
    merged += list(new.values())
    ordered = {k: doc[k] for k in ("project", "language", "version") if k in doc}
    ordered[key] = merged
    out.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {}
    if a.kind == "tc":
        for t in merged:
            counts[t.get("priority")] = counts.get(t.get("priority"), 0) + 1
    print(f"wrote {out}: {len(merged)} {'test cases' if a.kind == 'tc' else 'requirements'}"
          + (f" · priority {counts}" if counts else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
