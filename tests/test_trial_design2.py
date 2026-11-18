"""evals/keys/design2_grader.py and the reference deliverables of evals/trial-design2.

Run:  python -m unittest tests.test_trial_design2 -v
"""
import contextlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "evals" / "keys"
TRIAL = ROOT / "evals" / "trial-design2"
GRADER = KEYS / "design2_grader.py"
GOLD = KEYS / "design2_ref" / "gold"
NAIVE = KEYS / "design2_ref" / "naive"
SPEC = TRIAL / "girdiler" / "GUM-spesifikasyon-v3.2.md"

_spec = importlib.util.spec_from_file_location("design2_grader", GRADER)
dg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dg)

U_HEAD = dg.HEADERS["ucret"]
D_HEAD = dg.HEADERS["durum"]
B_HEAD = dg.HEADERS["bulgu"]
PATH = "TRANSFERE_VER > DAGITIMA_CIKAR > TESLIM_BASARISIZ(neden=ADRESTE_YOK) > SUBEYE_YONLENDIR"


def grade_with(**files):
    """Grade a copy of the gold folder in which the named files are replaced.
    Keyword = area key (ucret, durum, konfig, bulgu); value = full text, or None to delete."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "cikti"
        shutil.copytree(GOLD, d)
        for kind, text in files.items():
            p = d / dg.FILES[kind]
            if text is None:
                p.unlink()
            elif isinstance(text, bytes):
                p.write_bytes(text)
            else:
                p.write_text(text, encoding="utf-8", newline="\n")
        return dg.grade_folder(str(d))


def table(head, rows):
    return "\n".join([head] + rows) + "\n"


def penalties(res, kind):
    return [txt for _, txt in res["areas"][kind]["penalties"]]


class ReferenceDeliverables(unittest.TestCase):
    def test_selftest_passes(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = dg.selftest()
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn("SELFTEST PASSED", buf.getvalue())

    def test_gold_scores_the_maximum(self):
        res = dg.grade_folder(str(GOLD))
        self.assertEqual(res["max"], 100)
        self.assertEqual(res["final"], 100)
        for kind, area in res["areas"].items():
            self.assertEqual(area["penalties"], [], kind)
            self.assertEqual(area["over_budget"], 0, kind)
            self.assertLessEqual(area["rows_total"], dg.BUDGET[kind], kind)
            self.assertEqual(area["score"], area["max"], kind)
        self.assertEqual(sum(a["max"] for a in res["areas"].values()), 100)

    def test_naive_scores_at_most_a_quarter(self):
        res = dg.grade_folder(str(NAIVE))
        self.assertLessEqual(res["final"], 25)
        self.assertGreater(sum(len(a["penalties"]) for a in res["areas"].values()), 0)

    def test_grading_is_deterministic(self):
        a = json.dumps(dg.grade_folder(str(NAIVE)), sort_keys=True, default=str)
        b = json.dumps(dg.grade_folder(str(NAIVE)), sort_keys=True, default=str)
        self.assertEqual(a, b)

    def test_command_line_prints_score_last_and_writes_json(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "grade.json"
            run = subprocess.run([sys.executable, str(GRADER), str(GOLD), "--json", str(out)],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(run.returncode, 0, run.stderr)
            last = [ln for ln in run.stdout.splitlines() if ln.strip()][-1]
            self.assertRegex(last, r"^FINAL SCORE: 100 / 100\b")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["final"], 100)
        run = subprocess.run([sys.executable, str(GRADER), "--selftest"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        self.assertEqual(run.returncode, 0, run.stdout)


class TrialInputs(unittest.TestCase):
    def test_templates_have_the_graded_headers(self):
        for kind, name in dg.FILES.items():
            first = (TRIAL / "girdiler" / "sablonlar" / name).read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first, dg.HEADERS[kind], name)

    def test_template_example_rows_are_ignored_and_correct(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "cikti"
            shutil.copytree(TRIAL / "girdiler" / "sablonlar", d)
            res = dg.grade_folder(str(d))
            self.assertEqual([a["rows_total"] for a in res["areas"].values()], [0, 0, 0, 0])
            for name in ("ucret-testleri.csv", "durum-testleri.csv"):
                p = d / name
                p.write_text(p.read_text(encoding="utf-8").replace("ORNEK-", "X-"), encoding="utf-8")
            res = dg.grade_folder(str(d))
            self.assertEqual(res["areas"]["ucret"]["rows_total"], 2)
            self.assertEqual(res["areas"]["ucret"]["details"]["correct"], 2)
            self.assertEqual(res["areas"]["durum"]["details"]["correct"], 1)

    def test_task_states_the_budgets_the_grader_uses(self):
        task = (TRIAL / "TASK.md").read_text(encoding="utf-8")
        for kind, name in dg.FILES.items():
            m = re.search(re.escape(name) + r"`[^\n]*en fazla \*\*(\d+)\*\*", task)
            self.assertIsNotNone(m, name)
            self.assertEqual(int(m.group(1)), dg.BUDGET[kind], name)

    def test_spec_examples_follow_the_rules_except_the_planted_one(self):
        """Ek-A as printed in the specification against the oracle: A-4 alone is wrong (planted D1)."""
        rows = re.findall(r"^\| (A-\d) \|(.+)\|\s*$", SPEC.read_text(encoding="utf-8"), flags=re.M)
        self.assertEqual([r[0] for r in rows], ["A-%d" % i for i in range(1, 8)])

        def num(s):
            return s.strip().replace(".", "").replace(",", ".")
        wrong = {}
        for aid, rest in rows:
            c = [x.strip() for x in rest.split("|")]
            en, boy, yuk = [x.strip() for x in c[2].split("×")]
            o = dg.price({"musteri_tipi": c[0], "agirlik_kg": num(c[1]), "en_cm": en, "boy_cm": boy,
                          "yukseklik_cm": yuk, "bolge": c[3], "hizmet": c[4],
                          "kampanya_kodu": "" if c[5] == "—" else c[5],
                          "beyan_degeri": "" if c[6] == "—" else num(c[6]), "kabul_zamani": c[7]})
            self.assertEqual(o["accept_err"], [], aid)
            k = o["calc"]
            got = {"UA": "%.1f" % k["ua"], "TB": str(k["tb"]), "IT": str(k["it"]), "YE": str(k["ye"]),
                   "SP": str(k["sp"]), "KDV": str(k["kdv"]), "TU": str(k["tu"]),
                   "tarih": o["variants"][0]["teslim"].isoformat()}
            printed = dict(zip(("UA", "TB", "IT", "YE", "SP", "KDV", "TU"), (num(x) for x in c[8:15])))
            printed["tarih"] = c[15]
            self.assertEqual(len(o["variants"]), 1, aid)
            diff = sorted(key for key in got if got[key] != printed[key])
            if diff:
                wrong[aid] = diff
        self.assertEqual(wrong, {"A-4": ["KDV", "TU", "YE"]})

    def test_spec_calendar_matches_the_oracle(self):
        text = SPEC.read_text(encoding="utf-8")
        rows = re.findall(r"^\| (B-\d) \| (\d{4}-\d{2}-\d{2}) \| (\S+) \|", text, flags=re.M)
        names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.assertEqual({d.isoformat(): b for d, b in dg.HOLIDAYS.items()}, {d: b for b, d, _ in rows})
        for _, d, day in rows:
            self.assertEqual(names[dg.dt.date.fromisoformat(d).weekday()], day, d)


class ExactnessAndLeniency(unittest.TestCase):
    def test_bom_crlf_and_spaces_do_not_change_the_score(self):
        files = {}
        for kind, name in dg.FILES.items():
            text = (GOLD / name).read_text(encoding="utf-8")
            text = text.replace(";", " ;") if kind == "konfig" else text
            files[kind] = b"\xef\xbb\xbf" + text.replace("\n", "  \r\n").encode("utf-8") + b"\r\n\r\n"
        self.assertEqual(grade_with(**files)["final"], 100)

    def test_changed_header_or_separator_is_not_graded(self):
        text = (GOLD / dg.FILES["konfig"]).read_text(encoding="utf-8")
        for bad in (text.replace(";", ","), text.replace("teslim_noktasi", "teslimat"),
                    text.encode("utf-16")):
            res = grade_with(konfig=bad)
            self.assertFalse(res["areas"]["konfig"]["ok"])
            self.assertEqual(res["final"], 100 - 14)
        self.assertEqual(grade_with(konfig=None)["final"], 100 - 14)

    def test_codes_are_case_sensitive(self):
        res = grade_with(durum=table(D_HEAD, [
            "X1;TRANSFERE_VER > IPTAL(aktor=operator);KABUL;IADE_YOLUNDA;0;lower-case value is not a valid actor",
            "X2;TRANSFERE_VER > IPTAL(aktor=operator);ERR_GECERSIZ_GIRDI;TRANSFERDE;0;10.5 rule 3",
            "X3;transfere_ver;ERR_GECERSIZ_GIRDI;KABUL_EDILDI;0;10.5 rule 1",
        ]))
        self.assertEqual(res["areas"]["durum"]["details"]["correct"], 2)
        self.assertEqual(len(penalties(res, "durum")), 1)
        self.assertIn("X1", penalties(res, "durum")[0])
        res = grade_with(ucret=table(U_HEAD, [
            "X1;bireysel;2.00;20;20;10;YAKIN;STANDART;;;2028-03-06 10:15;KABUL;2.0;0.00;134.20;2028-03-09;",
            "X2;bireysel;2.00;20;20;10;YAKIN;STANDART;;;2028-03-06 10:15;ERR_GECERSIZ_GIRDI;;;;;",
        ]))
        self.assertEqual(res["areas"]["ucret"]["details"]["correct"], 1)
        self.assertEqual(len(penalties(res, "ucret")), 1)

    def test_wrong_expected_values_cost_points(self):
        base = "BIREYSEL;2.00;20;20;10;UZAK;STANDART;;;2028-03-07 10:00;KABUL;"
        res = grade_with(ucret=table(U_HEAD, [
            "OK;" + base + "2.0;0.00;172.54;2028-03-13;half-up: YE 8.775 -> 8.78",
            "ZEROS;" + base + "2;0;172.540;2028-03-13;same numbers, other number of zeros",
            "FLOAT;" + base + "2.0;0.00;172.52;2028-03-13;binary float gives YE 8.77",
            "COMMA;" + base + "2,0;0,00;172,54;2028-03-13;decimal comma is not the agreed format",
            "DATE;" + base + "2.0;0.00;172.54;13.03.2028;wrong date format",
            "BLANK;" + base + "2.0;0.00;;2028-03-13;incomplete, neither counted nor penalised",
            "ERRFILL;BIREYSEL;30.01;20;20;10;UZAK;STANDART;;;2028-03-07 10:00;ERR_AGIRLIK;30.5;;;;error with amounts",
        ]))
        area = res["areas"]["ucret"]
        self.assertEqual(area["details"]["correct"], 2)
        self.assertEqual(sorted(p.split()[2].rstrip(":") for p in penalties(res, "ucret")),
                         ["COMMA", "DATE", "ERRFILL", "FLOAT"])
        self.assertEqual(area["penalty"], 4 * dg.PEN_ROW)
        self.assertEqual(area["details"]["incomplete"], ["BLANK: blank beklenen_toplam"])
        self.assertEqual(area["score"], 0)      # an area never goes below zero

    def test_both_readings_are_accepted_at_the_planted_defects(self):
        cut = "BIREYSEL;2.00;20;20;10;YAKIN;EKSPRES;;;2028-03-21 17:00;KABUL;2.0;0.00;181.15;"
        two = "BIREYSEL;30.01;20;20;10;YAKIN;EKSPRES;;50000.01;2028-03-21 10:00;"
        res = grade_with(ucret=table(U_HEAD, [
            "A;" + cut + "2028-03-22;8.2: 17:00 is on time",
            "B;" + cut + "2028-03-23;2.4: 17:00 is late",
            "C;" + cut + "2028-03-24;neither reading",
            "D;" + two + "ERR_AGIRLIK;;;;;listed error first",
            "E;" + two + "ERR_BEYAN_LIMIT;;;;;unlisted error first",
            "F;" + two + "ERR_HACIM;;;;;not applicable",
        ]))
        self.assertEqual(res["areas"]["ucret"]["details"]["correct"], 4)
        self.assertEqual(sorted(p.split()[2].rstrip(":") for p in penalties(res, "ucret")), ["C", "F"])

    def test_invalid_precondition_is_a_wrong_row(self):
        res = grade_with(durum=table(D_HEAD, [
            "X1;DAGITIMA_CIKAR > TESLIM_BASARILI;KABUL;TESLIM_EDILDI;0;first event is rejected",
            "X2;" + PATH + " > SUBEDEN_TESLIM(gun=5);KABUL;TESLIM_EDILDI;1;fine",
            "X3;" + PATH + " > SUBEDEN_TESLIM(gun=5);KABUL;TESLIM_EDILDI;;counter left blank",
        ]))
        area = res["areas"]["durum"]
        self.assertEqual(area["details"]["correct"], 1)
        self.assertEqual(len(area["penalties"]), 1)
        self.assertIn("precondition", area["penalties"][0][1])
        self.assertEqual(len(area["details"]["incomplete"]), 1)


class BudgetsFindingsAndConstraints(unittest.TestCase):
    def test_rows_beyond_the_budget_are_ignored_and_cost_a_flat_penalty(self):
        gold = (GOLD / dg.FILES["konfig"]).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(gold) - 1, 23)
        extra = ["E1;WEB;BIREYSEL;STANDART;YAKIN;GONDERICI_KART;ADRES",
                 "E2;WEB;BIREYSEL;STANDART;YAKIN;GONDERICI_NAKIT;ADRES",      # KS-7, but beyond the budget
                 "E3;API;BIREYSEL;STANDART;YAKIN;CARI_HESAP;ADRES"]
        res = grade_with(konfig="\n".join(gold + extra) + "\n")
        area = res["areas"]["konfig"]
        self.assertEqual((area["rows_total"], area["rows_graded"], area["over_budget"]), (26, 24, 2))
        self.assertEqual([p for p, _ in area["penalties"]], [dg.PEN_BUDGET])
        self.assertEqual(area["score"], 14 - 2 - dg.PEN_BUDGET)     # C3 lost, flat penalty
        # the same rows first: coverage is cut off at row 24 and the violation is now inside the budget
        res = grade_with(konfig="\n".join(gold[:1] + extra + gold[1:]) + "\n")
        area = res["areas"]["konfig"]
        self.assertLess(area["items"]["C2"]["got"] + area["items"]["C1"]["got"], 12)
        self.assertEqual(sorted(p for p, _ in area["penalties"]), [dg.PEN_BUDGET, dg.PEN_ROW, dg.PEN_ROW])

    def test_unsupported_combinations_cost_points_and_do_not_cover(self):
        for row, ks in (("X;MOBIL;BIREYSEL;AYNI_GUN;YAKIN;GONDERICI_KART;ADRES", "KS-1"),
                        ("X;WEB;BIREYSEL;STANDART;YAKIN;CARI_HESAP;ADRES", "KS-2"),
                        ("X;API;BIREYSEL;STANDART;YAKIN;GONDERICI_KART;ADRES", "KS-3"),
                        ("X;WEB;KURUMSAL;STANDART;YAKIN;ALICI_ODEMELI;ADRES", "KS-4"),
                        ("X;GISE;BIREYSEL;STANDART;YAKIN;ALICI_ODEMELI;OTOMAT", "KS-5"),
                        ("X;MOBIL;BIREYSEL;AYNI_GUN;SEHIRICI;GONDERICI_KART;SUBE", "KS-6"),
                        ("X;MOBIL;BIREYSEL;STANDART;YAKIN;GONDERICI_NAKIT;ADRES", "KS-7"),
                        ("X;Web;BIREYSEL;STANDART;YAKIN;GONDERICI_KART;ADRES", "unknown value")):
            res = grade_with(konfig=table(dg.HEADERS["konfig"], [row]))
            self.assertEqual(len(penalties(res, "konfig")), 1, row)
            self.assertIn(ks, penalties(res, "konfig")[0])
            self.assertEqual(res["areas"]["konfig"]["details"]["valid"], 0)

    def test_findings_are_graded_by_reference_and_type(self):
        res = grade_with(bulgu=table(B_HEAD, [
            "B-01;Ek-A Örnek 4;ÇELİŞKİ;other spelling of the same reference and type",
            "B-02;8.2 / 2.4;BELIRSIZLIK;both places, defensible type",
            "B-03;9.3;BELIRSIZLIK;only one of the two places: not credited",
            "B-04;G-11;ERISILEMEZ;dead transition",
            "B-05;G14;ONERI;a suggestion is never a defect",
            "B-06;10.6;BELIRSIZLIK;unit",
            "B-07;G11;ERISILEMEZ;duplicate, neutral",
        ]))
        area = res["areas"]["bulgu"]
        self.assertEqual({k: v["got"] for k, v in area["items"].items()},
                         {"D1": 3, "D2": 4, "D3": 0, "D4": 5, "D5": 4})
        self.assertEqual(area["penalties"], [])
        self.assertEqual(area["score"], 16)

    def test_traps_reported_as_defects_cost_points(self):
        res = grade_with(bulgu=table(B_HEAD, [
            "B-01;A-2;CELISKI;trap T1: the example is right (8.4)",
            "B-02;A-5,6.2;CELISKI;trap T1: the example is right (acceptance date)",
            "B-03;G16;ERISILEMEZ;trap T2: reachable through G12",
            "B-04;8.2,8.6;CELISKI;trap T3: cut-off is not the closing time",
            "B-05;4.2,4.5;CELISKI;trap T4: UA can exceed GA through HA",
            "B-06;A-4;CELISKI;the real one",
            "B-07;G16;ONERI;a note is not a defect claim",
            "B-08;6.3;BELIRSIZLIK;unplanted remark, neutral",
        ]))
        area = res["areas"]["bulgu"]
        self.assertEqual(len(area["penalties"]), 5)
        self.assertEqual(area["penalty"], 5 * dg.PEN_TRAP)
        self.assertEqual(area["points"], 3)
        self.assertEqual(area["score"], 0)
        self.assertEqual(len(area["details"]["neutral_rows"]), 2)

    def test_one_row_is_one_finding(self):
        res = grade_with(bulgu=table(B_HEAD, [
            "B-01;A-4,2.4,8.2,G11;CELISKI;several findings in one row earn one defect",
            "B-02;A-4,2.4,8.2,G11,7.2,9.3;CELISKI;more than four places: ignored",
            "B-03;10.6;KRITIK;unknown type: ignored",
        ]))
        area = res["areas"]["bulgu"]
        self.assertEqual(area["points"], 3)
        self.assertEqual(len(area["details"]["ignored_rows"]), 2)

    def test_state_model_facts(self):
        live, pairs = dg.model_facts()
        self.assertEqual(sorted(set(dg.ALL_G) - live), ["G11"])       # planted dead transition
        self.assertIn("G16", live)                                   # trap: looks dead, is not
        self.assertEqual(len(pairs), 29)
        combos, cpairs, triples = dg.cfg_facts()
        self.assertEqual((len(cpairs), len(triples)), (152, 19))


if __name__ == "__main__":
    unittest.main()
