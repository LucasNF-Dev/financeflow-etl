"""Contratos HTTP paginados dos ERPs Alpha e Beta."""

import json
from importlib.resources import files
from secrets import compare_digest
from threading import Lock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from financeflow.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="FinanceFlow Mock API", version="0.1.0")
    alpha = sorted(json.loads(files("mock_api").joinpath("fixtures/alpha.json").read_text()), key=lambda row: row["id"])
    beta = sorted(json.loads(files("mock_api").joinpath("fixtures/beta.json").read_text()), key=lambda row: row["codigo"])
    failed_sources: set[str] = set()
    failure_lock = Lock()

    def authorize_alpha(authorization: Annotated[str | None, Header()] = None):
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not compare_digest(token.encode(), settings.alpha_token.encode()):
            raise HTTPException(401, "Credencial inválida", headers={"WWW-Authenticate": "Bearer"})

    def authorize_beta(x_api_key: Annotated[str | None, Header()] = None):
        if not compare_digest((x_api_key or "").encode(), settings.beta_api_key.encode()):
            raise HTTPException(401, "Credencial inválida")

    def simulate_failure(source: str, page: int):
        if page != 2 or settings.failure_mode == "none":
            return
        with failure_lock:
            if settings.failure_mode == "always" or source not in failed_sources:
                failed_sources.add(source)
                raise HTTPException(503, "Falha sintética de demonstração")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/alpha/transactions", dependencies=[Depends(authorize_alpha)])
    def alpha_transactions(
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1)] = 2,
    ):
        simulate_failure("alpha", page)
        start = (page - 1) * page_size
        return {"data": alpha[start:start + page_size], "next_page": page + 1 if start + page_size < len(alpha) else None}

    @app.get("/beta/lancamentos", dependencies=[Depends(authorize_beta)])
    def beta_transactions(
        pagina: Annotated[int, Query(ge=1)] = 1,
        limite: Annotated[int, Query(ge=1)] = 2,
    ):
        simulate_failure("beta", pagina)
        start = (pagina - 1) * limite
        return {"lancamentos": beta[start:start + limite], "pagina": pagina, "total_paginas": (len(beta) + limite - 1) // limite}

    return app
