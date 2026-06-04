"""Config loader — reads .privacy-router.config.yaml with env var resolution.

Public API
----------
load_config
    Load config from a YAML file, returning a validated
    :class:`PrivacyRouterConfig`.
resolve_model
    Look up a :class:`ModelSpec` by id from the config's model registry.

Examples
--------
>>> from config.loader import load_config
>>> config = load_config()
>>> config.extractor.model
'openrouter/mistralai/ministral-3b-2512'
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .schemas import ModelSpec, PrivacyRouterConfig

# ── Default locations to search ──────────────────────────────────────────────

_DEFAULT_PATH = Path(".privacy-router.config.yaml")


# ── Public API ───────────────────────────────────────────────────────────────


def load_config(path: str | Path | None = None) -> PrivacyRouterConfig:
    """Load and validate the Privacy Router config from a YAML file.

    Parameters
    ----------
    path : str, Path, or None
        Path to a YAML config file.  If ``None``, reads
        ``.privacy-router.config.yaml`` from CWD.

    Returns
    -------
    PrivacyRouterConfig
        Validated configuration object.

    Raises
    ------
    FileNotFoundError
        If no config file is found at the given or default paths.
    ValueError
        If the YAML is malformed or fails Pydantic validation.

    Examples
    --------
    >>> config = load_config()
    >>> config.extractor.model
    'openrouter/mistralai/ministral-3b-2512'
    """
    if path is not None:
        config_path = Path(path)
    else:
        config_path = _DEFAULT_PATH
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Copy .privacy-router.config.yaml.example to .privacy-router.config.yaml "
            "and edit it to match your setup."
        )

    raw = _read_yaml(config_path)
    resolved = _resolve_env_vars(raw)
    return PrivacyRouterConfig.model_validate(resolved)


def resolve_model(config: PrivacyRouterConfig, model_id: str) -> ModelSpec:
    """Find a model spec by id in the config's model registry.

    Parameters
    ----------
    config : PrivacyRouterConfig
        The loaded configuration.
    model_id : str
        The model id to look up.

    Returns
    -------
    ModelSpec
        The matching model spec.

    Raises
    ------
    KeyError
        If *model_id* is not found in the registry.

    Examples
    --------
    >>> config = load_config()
    >>> spec = resolve_model(config, "openrouter/mistralai/ministral-3b-2512")
    >>> spec.tier
    'edge'
    """
    for m in config.models:
        if m.id == model_id:
            return m
    raise KeyError(
        f"Model {model_id!r} not found in config.models. "
        f"Available: {[m.id for m in config.models]}"
    )


# ── Internal helpers ─────────────────────────────────────────────────────────


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping.")
    return data


def _resolve_env_vars(data: Any) -> Any:
    """Recursively resolve ``${ENV_VAR}`` and ``${ENV_VAR:default}`` in strings.

    Examples
    --------
    >>> os.environ["TEST_KEY"] = "hello"
    >>> _resolve_env_vars({"key": "${TEST_KEY}"})
    {'key': 'hello'}
    >>> _resolve_env_vars({"key": "${MISSING:world}"})
    {'key': 'world'}
    """
    import re

    _ENV_RE = re.compile(r"\$\{(\w+)(?::([^}]*))?\}")

    def _resolve(value: str) -> str:
        def _replace(m: re.Match) -> str:
            var = m.group(1)
            default = m.group(2)
            return os.environ.get(var, default if default is not None else m.group(0))
        return _ENV_RE.sub(_replace, value)

    if isinstance(data, dict):
        return {k: _resolve_env_vars(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_resolve_env_vars(v) for v in data]
    if isinstance(data, str):
        return _resolve(data)
    return data
