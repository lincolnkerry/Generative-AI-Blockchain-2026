"""Tests for agents.judge."""

from agents.judge import Judge, Judgment, MeaningfulnessAssessment


class TestJudge:
    def test_no_records(self):
        judge = Judge()
        sensitivity = {"is_sensitive": False, "rationale": "test"}
        judgment = judge.classify(sensitivity, [], "hello world")
        assert judgment.policy_action == "allow"
        assert judgment.meaningful_after_masking.is_meaningful_after_masking is True

    def test_judgment_to_dict(self):
        judgment = Judgment(
            meaningful_after_masking=MeaningfulnessAssessment(
                is_meaningful_after_masking=True, rationale="test"
            ),
            policy_action="mask_and_send",
            strategy="테스트",
            rationale="테스트",
        )
        d = judgment.to_dict()
        assert "policy_action" in d
        assert "meaningful_after_masking" in d
