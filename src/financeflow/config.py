"""Configuração do mock; nenhuma credencial real é necessária."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    alpha_token: str
    beta_api_key: str
    failure_mode: str = "none"

    def __post_init__(self):
        if not self.alpha_token.strip() or not self.beta_api_key.strip():
            raise ValueError("ALPHA_TOKEN e BETA_API_KEY devem ser preenchidos")
        if self.failure_mode not in {"none", "once", "always"}:
            raise ValueError("MOCK_FAILURE_MODE deve ser none, once ou always")

    @classmethod
    def from_env(cls):
        return cls(
            alpha_token=os.environ.get("ALPHA_TOKEN", ""),
            beta_api_key=os.environ.get("BETA_API_KEY", ""),
            failure_mode=os.environ.get("MOCK_FAILURE_MODE", "none"),
        )
