"""evals/keys/design_grader.py: state-transition rows with a non-canonical aktor value."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("design_grader", ROOT / "evals/keys/design_grader.py")
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)
HEADER = "test_id;odeme_yontemi;olay_dizisi;beklenen_son_olay_sonucu;beklenen_son_durum;aciklama"


def grade(rows):
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "durum-gecis-testleri.csv"
        p.write_text(chr(10).join([HEADER] + rows) + chr(10), encoding="utf-8")
        return dg.grade_states(str(p))


class AktorCaseTests(unittest.TestCase):
    def test_lowercase_aktor_accepts_strict_and_lenient_reading(self):
        res = grade([
            "T-1;KREDI_KARTI;IPTAL(aktor=musteri);ERR_GECERSIZ_GIRDI;ODEME_BEKLENIYOR;strict",
            "T-2;KREDI_KARTI;IPTAL(aktor=musteri);KABUL;IPTAL_EDILDI;lenient",
            "T-3;KREDI_KARTI;IPTAL(aktor=MUSTERI);KABUL;IPTAL_EDILDI;canonical",
        ])
        self.assertEqual(res["errors"], [])
        self.assertEqual(len(res["correct"]), 3)

    def test_canonical_aktor_is_never_invalid_input(self):
        res = grade(["T-1;KREDI_KARTI;IPTAL(aktor=MUSTERI);ERR_GECERSIZ_GIRDI;ODEME_BEKLENIYOR;wrong"])
        self.assertEqual(len(res["errors"]), 1)

    def test_strict_reading_does_not_override_rule_order(self):
        # 10.5.2 comes before 10.5.3: IPTAL is not in the table for KARGODA, so the answer is ERR_GECERSIZ_GECIS
        res = grade(["T-1;KREDI_KARTI;ODEME_BASARILI > HAZIRLAMAYA_BASLA > KARGOYA_VER > IPTAL(aktor=musteri);"
                     "ERR_GECERSIZ_GIRDI;KARGODA;wrong"])
        self.assertEqual(len(res["errors"]), 1)


if __name__ == "__main__":
    unittest.main()
