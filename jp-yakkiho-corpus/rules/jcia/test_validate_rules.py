import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema


MODULE_PATH = Path(__file__).with_name("validate_rules.py")
SPEC = importlib.util.spec_from_file_location("validate_rules", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RuleValidationTest(unittest.TestCase):
    def test_current_rules_are_valid(self):
        self.assertEqual(MODULE.validate(MODULE.load_rows()), [])

    def test_policy_change_is_rejected(self):
        rows = MODULE.load_rows()
        rows[0] = copy.deepcopy(rows[0])
        rows[0]["output_policy"] = "legal_violation"
        self.assertTrue(any("output policy changed" in e for e in MODULE.validate(rows)))

    def test_invented_unresolved_locator_is_rejected(self):
        rows = MODULE.load_rows()
        row = next(copy.deepcopy(r) for r in rows if r["exact_basis_unresolved"])
        if row["legal_basis"]:
            basis = next(b for b in row["legal_basis"] if b["exact_basis_unresolved"])
        else:
            basis = copy.deepcopy(row["supporting_guidance"][0])
            basis["exact_basis_unresolved"] = True
            row["legal_basis"].append(basis)
        basis["locator"] = "invented"
        self.assertTrue(any("must not invent" in e for e in MODULE.validate([row])))

    def test_schema_rejects_additional_property(self):
        rows = MODULE.load_rows()
        rows[0] = copy.deepcopy(rows[0])
        rows[0]["unexpected"] = True
        self.assertTrue(any("schema" in e and "unexpected" in e for e in MODULE.validate(rows)))

    def test_anchor_owner_tampering_is_rejected(self):
        rows = MODULE.load_rows()
        rows[0] = copy.deepcopy(rows[0])
        rows[0]["legal_basis"][0]["source_id"] = "JP-AD-001"
        self.assertTrue(any("anchor ownership mismatch" in e for e in MODULE.validate(rows)))

    def test_jcia_locator_tampering_is_rejected(self):
        rows = MODULE.load_rows()
        rows[0] = copy.deepcopy(rows[0])
        rows[0]["supporting_guidance"][0]["locator"] = "JCIA invented / printed p.999 / PDF p.999"
        self.assertTrue(any("outside reviewed allowlist" in e for e in MODULE.validate(rows)))

    def test_mhlw_legal_locator_tampering_is_rejected(self):
        rows = MODULE.load_rows()
        target = next(i for i, row in enumerate(rows) if any(b["source_id"] == "JP-AD-002" for b in row["legal_basis"]))
        rows[target] = copy.deepcopy(rows[target])
        basis = next(b for b in rows[target]["legal_basis"] if b["source_id"] == "JP-AD-002")
        basis["locator"] = "해설 第9-99"
        self.assertTrue(any("legal source/locator/anchor is outside reviewed allowlist" in e for e in MODULE.validate(rows)))

    def test_duplicate_risk_type_is_rejected(self):
        rows = MODULE.load_rows()
        rows[1] = copy.deepcopy(rows[1])
        rows[1]["risk_type"] = rows[0]["risk_type"]
        self.assertTrue(any("duplicate risk_type" in e for e in MODULE.validate(rows)))

    def test_finding_unresolved_requires_escalation(self):
        schema = json.loads(MODULE.read_utf8_nfc_lf(MODULE.FINDING_SCHEMA))
        rule = next(r for r in MODULE.load_rows() if r["rule_id"] == "JCIA-R-032")
        finding = {
            "finding_id": "F-1", "rule_id": "JCIA-R-032",
            "ai_status": "검토 후보", "human_review_status": "미검토",
            "conclusion": "관련 조항과 충돌 가능성이 있는 문제 후보",
            "matched_text": "", "review_reason": "근거 위치 미확인",
            "legal_basis": [], "supporting_guidance": rule["supporting_guidance"], "required_evidence": [],
            "exact_basis_unresolved": True, "expert_escalation": False,
            "disclaimer": "AI 결과는 JCIA 업계 자율기준에 따른 사전검토 보조이며 법률판단이나 최종 승인 결과가 아닙니다."
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(finding, schema)

    def test_finding_forbidden_conclusion_is_rejected(self):
        schema = json.loads(MODULE.read_utf8_nfc_lf(MODULE.FINDING_SCHEMA))
        rule = MODULE.load_rows()[0]
        finding = {
            "finding_id": "F-2", "rule_id": "JCIA-R-001",
            "ai_status": "검토 후보", "human_review_status": "미검토",
            "conclusion": "위법 확정", "matched_text": "", "review_reason": "후보",
            "legal_basis": rule["legal_basis"], "supporting_guidance": rule["supporting_guidance"], "required_evidence": [],
            "exact_basis_unresolved": False, "expert_escalation": False,
            "disclaimer": "AI 결과는 JCIA 업계 자율기준에 따른 사전검토 보조이며 법률판단이나 최종 승인 결과가 아닙니다."
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(finding, schema)

    def test_crlf_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.jsonl"
            path.write_bytes(b'{"rule_id":"X"}\r\n')
            with self.assertRaisesRegex(ValueError, "CR/CRLF"):
                MODULE.load_rows(path)


if __name__ == "__main__":
    unittest.main()
