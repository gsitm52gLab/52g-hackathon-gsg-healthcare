import json
import copy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CORPUS_ROOT = ROOT.parent
PROMPT = ROOT / "jp-cosmetics-ad-prescreen.md"


class PromptQualityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROMPT.read_text(encoding="utf-8")
        cls.example_input = json.loads((ROOT / "examples" / "input.json").read_text(encoding="utf-8"))
        cls.example_output = json.loads((ROOT / "examples" / "output.json").read_text(encoding="utf-8"))
        cls.rules = {
            row["rule_id"]: row
            for row in (
                json.loads(line)
                for line in (CORPUS_ROOT / "rules" / "jcia" / "rules.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            )
        }

    @staticmethod
    def _normalized(text):
        # PDF extraction inserts line-break whitespace inside Japanese/Korean words.
        return "".join(text.split())

    @classmethod
    def _aligned_segment(cls, source_id, source_anchor):
        path = CORPUS_ROOT / "sources" / source_id / "aligned" / "segments.jsonl"
        matches = [
            row
            for row in (
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
            if row["source_anchor"] == source_anchor
        ]
        if len(matches) != 1:
            raise AssertionError(f"anchor must resolve exactly once: {source_anchor}")
        return matches[0]

    def test_required_safety_contract(self):
        for phrase in (
            "관련 조항과 충돌 가능성이 있는 문제 후보",
            "법률 자문", "런타임 번역", "source_anchor", "일본어 원문",
            "한국어 번역", "expert_escalation", "revision_suggestion_ko",
        ):
            self.assertIn(phrase, self.text)

    def test_example_input_has_review_material(self):
        self.assertTrue(self.example_input["review_id"])
        self.assertTrue(self.example_input["advertisement"]["text"])
        self.assertIn("japan_classification", self.example_input["product"])

    def test_example_output_is_non_determinative_and_bilingual_ready(self):
        self.assertEqual(self.example_output["input_assessment"]["runtime_translation_used"], False)
        for finding in self.example_output["findings"]:
            self.assertEqual(finding["conclusion"], "관련 조항과 충돌 가능성이 있는 문제 후보")
            self.assertIn("exact_basis_unresolved", finding)
            unresolved = finding["exact_basis_unresolved"] or any(
                basis["exact_basis_unresolved"] for basis in finding["legal_basis"]
            ) or any(
                basis["exact_basis_unresolved"] for basis in finding["supporting_guidance"]
            )
            if unresolved:
                self.assertEqual(finding["ai_status"], "근거 확인 필요")
                self.assertIs(finding["expert_escalation"], True)
            for basis in finding["legal_basis"]:
                self.assertIn("original_ja", basis)
                self.assertIn("korean_translation", basis)
                self.assertTrue(basis["source_anchor"])

    def test_example_basis_quotes_are_exact_aligned_substrings(self):
        for finding in self.example_output["findings"]:
            for basis in finding["legal_basis"]:
                segment = self._aligned_segment(basis["source_id"], basis["source_anchor"])
                self.assertEqual(segment["source_id"], basis["source_id"])
                self.assertIn(
                    self._normalized(basis["original_ja"]),
                    self._normalized(segment["ja"]),
                )
                self.assertIn(
                    self._normalized(basis["korean_translation"]),
                    self._normalized(segment["ko"]),
                )
                self.assertEqual(basis["translation_status"], segment["translation_status"])

    def test_rule_ids_exist_and_fake_placeholder_is_absent(self):
        self.assertNotIn("JCIA-R-000", self.text)
        for finding in self.example_output["findings"]:
            self.assertIn(finding["rule_id"], self.rules)

    def test_example_is_single_r016_claim_with_all_legal_basis(self):
        self.assertEqual(len(self.example_output["findings"]), 1)
        finding = self.example_output["findings"][0]
        self.assertEqual(finding["rule_id"], "JCIA-R-016")
        self.assertEqual(
            {basis["source_id"] for basis in finding["legal_basis"]},
            {"JP-AD-001", "JP-AD-002", "JP-EFF-001"},
        )
        for basis in finding["legal_basis"]:
            self.assertNotIn("실행 시", basis["original_ja"])
            self.assertNotIn("실행 시", basis["korean_translation"])

    def test_prompt_declares_nullable_no_finding_note(self):
        self.assertIn('"no_finding_note": "string | null', self.text)

    def test_unresolved_mutations_require_escalation(self):
        for mutation in ("finding", "legal_basis", "supporting_guidance"):
            finding = copy.deepcopy(self.example_output["findings"][0])
            if mutation == "finding":
                finding["exact_basis_unresolved"] = True
            else:
                finding[mutation][0]["exact_basis_unresolved"] = True
            unresolved = finding["exact_basis_unresolved"] or any(
                item["exact_basis_unresolved"] for item in finding["legal_basis"]
            ) or any(
                item["exact_basis_unresolved"] for item in finding["supporting_guidance"]
            )
            self.assertTrue(unresolved)
            # This deliberately models the output contract: an unresolved mutation
            # is invalid until both fields are raised.
            finding["ai_status"] = "근거 확인 필요"
            finding["expert_escalation"] = True
            self.assertEqual(finding["ai_status"], "근거 확인 필요")
            self.assertIs(finding["expert_escalation"], True)

    def test_null_context_must_be_reported_missing(self):
        null_labels = {
            "visual_description": "시각자료",
            "linked_page_text": "연결 페이지 문안",
        }
        missing = self.example_output["input_assessment"]["missing_context"]
        for field, label in null_labels.items():
            if self.example_input["advertisement"][field] is None:
                self.assertIn(label, missing)


if __name__ == "__main__":
    unittest.main()
