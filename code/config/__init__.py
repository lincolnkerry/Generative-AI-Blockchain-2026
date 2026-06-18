"""Privacy Router — Config package.

Centralised configuration for the Privacy Router pipeline.
Models, agents, and LLM parameters are declared in a single YAML file
(``.privacy-router.config.yaml``) and validated through Pydantic.

Public API
----------
PrivacyRouterConfig
    Root config model.
ModelSpec
    A single model entry in the registry.
AgentConfig
    Per-agent model + LLM parameter configuration.
LLMConfig
    LLM call-level knobs (temperature, max_tokens).
load_config
    Load and validate a YAML config file.
resolve_model
    Look up a ModelSpec by id from the config's model registry.

Examples
--------
>>> from config import load_config, resolve_model
>>> config = load_config()
>>> spec = resolve_model(config, config.extractor.model)
>>> spec.tier
'edge'
"""

from .loader import load_config, resolve_model
from .schemas import AgentConfig, LLMConfig, ModelSpec, PrivacyRouterConfig

__all__ = [
    "PrivacyRouterConfig",
    "ModelSpec",
    "AgentConfig",
    "LLMConfig",
    "load_config",
    "resolve_model",
]
