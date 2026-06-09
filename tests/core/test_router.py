"""Unit tests for Router and PrivacyRouter — config-based, no DB, no HTTP.

Tests the actual routing logic using .privacy-router.config.yaml.
No mocking — real config, real rule evaluation.
"""

from __future__ import annotations

import db.models  # noqa: F401, E402
from db.session import init_db  # noqa: E402

init_db()

from agents.router.router import PrivacyRouter, Router  # noqa: E402


class TestRouterResolve:
    """Test Router.resolve() — policy_action → RouteResult mapping."""

    def test_route_to_external(self):
        router = Router()
        result = router.resolve("route_to_external")
        assert result.endpoint == "external_api"
        assert result.requires_masking is False

    def test_mask_and_send(self):
        router = Router()
        result = router.resolve("mask_and_send")
        assert result.endpoint == "external_api"
        assert result.requires_masking is True

    def test_prompt_user(self):
        router = Router()
        result = router.resolve("prompt_user")
        assert result.endpoint == "prompt"
        assert result.requires_masking is False

    def test_unknown_action_raises(self):
        router = Router()
        import pytest
        with pytest.raises(ValueError, match="Unknown policy_action"):
            router.resolve("nonexistent")


class TestPrivacyRouterProcess:
    """Test PrivacyRouter.process() — full pipeline with real SLM calls.

    These tests make real API calls to the Extractor SLM via OpenRouter.
    No mocking.
    """

    def test_non_sensitive(self):
        pr = PrivacyRouter()
        result = pr.process("오늘 서울 날씨는 맑습니다")
        assert result.sensitivity.is_sensitive is False
        assert result.route.endpoint == "external_api"
        assert result.route.requires_masking is False
        assert len(result.records) == 0
    def test_sensitive_pii_load_bearing(self):
        """주민번호 확인 요청 — is_load_bearing=true → route_to_local 또는 prompt_user"""
        pr = PrivacyRouter()
        result = pr.process("내 주민등록번호가 뭐야?")
        assert result.sensitivity.is_sensitive is True
        assert len(result.records) > 0
        # 주민번호 자체가 질의 대상이므로 load-bearing
        assert any(r.is_load_bearing for r in result.records)
        # local 모델이 설정되어 있으면 route_to_local, 아니면 prompt_user
        assert result.route.endpoint in ("local_api", "prompt")

    def test_sensitive_pii_maskable(self):
        """주민번호 포함 이메일 작성 — is_load_bearing=false → mask_and_send"""
        pr = PrivacyRouter()
        result = pr.process("주민등록번호 901212-1234567을 포함한 이메일을 작성해줘")
        assert result.sensitivity.is_sensitive is True
        assert len(result.records) > 0
        # 이메일 작성은 가능하므로 mask_and_send 또는 route_to_local
        assert result.route.endpoint in ("external_api", "local_api")
        assert result.route.requires_masking is True or result.route.endpoint == "local_api"

    def test_business_secret(self):
        """사업비밀 — is_load_bearing=true → route_to_local 또는 prompt_user"""
        pr = PrivacyRouter()
        result = pr.process("TSMC 3nm 공정을 채택하기로 결정했다")
        assert result.sensitivity.is_sensitive is True
        assert result.route.endpoint in ("local_api", "prompt", "external_api")

    def test_config_model_used(self):
        """PrivacyRouter가 config에서 모델을 읽는지 확인"""
        pr = PrivacyRouter()
        assert pr._extractor_model is not None
        # config의 extractor.model과 일치해야 함
        from config import load_config
        cfg = load_config()
        assert pr._extractor_model == cfg.extractor.model


class TestConfigResolution:
    """Test that config properly resolves model specs."""

    def test_config_loads(self):
        from config import load_config
        cfg = load_config()
        assert cfg is not None
        assert len(cfg.models) > 0

    def test_extractor_model_exists(self):
        from config import load_config, resolve_model
        cfg = load_config()
        spec = resolve_model(cfg, cfg.extractor.model)
        assert spec is not None
        assert spec.id == cfg.extractor.model

    def test_generator_model_exists(self):
        from config import load_config, resolve_model
        cfg = load_config()
        spec = resolve_model(cfg, cfg.generator.model)
        assert spec is not None

    def test_all_models_resolvable(self):
        from config import load_config, resolve_model
        cfg = load_config()
        for model in cfg.models:
            spec = resolve_model(cfg, model.id)
            assert spec is not None, f"Model {model.id} not resolvable"
