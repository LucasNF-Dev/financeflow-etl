"""Contratos verificados com expectativas independentes das fixtures de produção."""

import pytest
from fastapi.testclient import TestClient

from financeflow.config import Settings
from mock_api.main import create_app


SETTINGS = Settings("alpha-test", "beta-test")
ALPHA_HEADERS = {"Authorization": "Bearer alpha-test"}
BETA_HEADERS = {"X-API-Key": "beta-test"}


@pytest.fixture
def client():
    with TestClient(create_app(SETTINGS)) as client:
        yield client


@pytest.mark.parametrize("size", [1, 2, 3, 8])
def test_complete_contracts(client, size):
    alpha = []
    page = 1
    for _ in range(6):
        response = client.get("/alpha/transactions", params={"page": page, "page_size": size}, headers=ALPHA_HEADERS)
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"data", "next_page"}
        assert 0 < len(body["data"]) <= size
        alpha.extend(body["data"])
        if body["next_page"] is None:
            break
        assert body["next_page"] == page + 1
        page = body["next_page"]
    else:
        pytest.fail("Alpha não encerrou")

    beta = []
    total_pages = (3 + size - 1) // size
    for page in range(1, total_pages + 1):
        response = client.get("/beta/lancamentos", params={"pagina": page, "limite": size}, headers=BETA_HEADERS)
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"lancamentos", "pagina", "total_paginas"}
        assert body["pagina"] == page
        assert body["total_paginas"] == total_pages
        assert 0 < len(body["lancamentos"]) <= size
        beta.extend(body["lancamentos"])

    assert len(alpha) + len(beta) == 8
    assert [row["id"] for row in alpha] == ["A-1", "A-2", "A-2", "A-3", "A-X"]
    assert alpha[1] == alpha[2]
    assert [(r["company_id"], r["amount"], r["competence_date"], r["payment_date"], r["status"]) for r in alpha] == [
        ("C1", "3000.00", "2026-09-30", "2026-10-02", "PAID"),
        ("C1", "-1200.00", "2026-10-01", "2026-10-03", "PAID"),
        ("C1", "-1200.00", "2026-10-01", "2026-10-03", "PAID"),
        ("C1", "500.00", "2026-10-02", None, "OPEN"),
        ("C1", "abc", "2026-10-02", None, "OPEN"),
    ]
    assert [row["codigo"] for row in beta] == ["B-1", "B-2", "B-3"]
    assert [(r["empresa"], r["valor"], r["tipo"], r["competencia"], r["pagamento"], r["situacao"]) for r in beta] == [
        ("C1", "2500,00", "RECEITA", "02/10/2026", "03/10/2026", "PAGO"),
        ("C1", "800,00", "DESPESA", "30/09/2026", "01/10/2026", "PAGO"),
        ("C1", "200,00", "DESPESA", "04/10/2026", None, "CANCELADO"),
    ]
    assert all(set(r) == {"id", "company_id", "description", "amount", "category", "competence_date", "payment_date", "status"} for r in alpha)
    assert all(set(r) == {"codigo", "empresa", "historico", "valor", "tipo", "categoria", "competencia", "pagamento", "situacao"} for r in beta)
    assert all(r["description"].strip() and r["category"] for r in alpha)
    assert all(r["historico"].strip() and r["categoria"] for r in beta)


def test_defaults_and_end(client):
    assert client.get("/alpha/transactions", headers=ALPHA_HEADERS).json()["next_page"] == 2
    assert client.get("/beta/lancamentos", headers=BETA_HEADERS).json()["total_paginas"] == 2
    assert client.get("/alpha/transactions?page=3", headers=ALPHA_HEADERS).json()["next_page"] is None
    assert client.get("/alpha/transactions?page=4", headers=ALPHA_HEADERS).json() == {"data": [], "next_page": None}
    assert client.get("/beta/lancamentos?pagina=2", headers=BETA_HEADERS).json()["pagina"] == 2
    assert client.get("/beta/lancamentos?pagina=3", headers=BETA_HEADERS).json() == {"lancamentos": [], "pagina": 3, "total_paginas": 2}


@pytest.mark.parametrize("path,headers", [
    ("/alpha/transactions", {}),
    ("/alpha/transactions", {"Authorization": "Bearer wrong"}),
    ("/alpha/transactions", {"Authorization": "Basic alpha-test"}),
    ("/alpha/transactions", {"Authorization": "Bearer"}),
    ("/alpha/transactions", BETA_HEADERS),
    ("/beta/lancamentos", {}),
    ("/beta/lancamentos", {"X-API-Key": "wrong"}),
    ("/beta/lancamentos", ALPHA_HEADERS),
])
def test_authentication(client, path, headers):
    response = client.get(path, headers=headers)
    assert response.status_code == 401
    assert "alpha-test" not in response.text and "beta-test" not in response.text
    if path.startswith("/alpha"):
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("path,headers", [
    ("/alpha/transactions?page=0", ALPHA_HEADERS),
    ("/alpha/transactions?page_size=0", ALPHA_HEADERS),
    ("/alpha/transactions?page=-1", ALPHA_HEADERS),
    ("/alpha/transactions?page=x", ALPHA_HEADERS),
    ("/beta/lancamentos?pagina=0", BETA_HEADERS),
    ("/beta/lancamentos?limite=0", BETA_HEADERS),
    ("/beta/lancamentos?pagina=-1", BETA_HEADERS),
    ("/beta/lancamentos?limite=x", BETA_HEADERS),
])
def test_invalid_pagination(client, path, headers):
    assert client.get(path, headers=headers).status_code == 422


def test_health_and_restart(client):
    assert client.get("/health").json() == {"status": "ok"}
    with TestClient(create_app(SETTINGS)) as restarted:
        for path, headers in [("/alpha/transactions?page_size=8", ALPHA_HEADERS), ("/beta/lancamentos?limite=8", BETA_HEADERS)]:
            assert client.get(path, headers=headers).json() == restarted.get(path, headers=headers).json()


@pytest.mark.parametrize("mode,expected", [("once", 200), ("always", 503)])
def test_failure_modes(mode, expected):
    settings = Settings("alpha-test", "beta-test", mode)
    for path, headers in [("/alpha/transactions?page=2", ALPHA_HEADERS), ("/beta/lancamentos?pagina=2", BETA_HEADERS)]:
        with TestClient(create_app(settings)) as client:
            assert client.get(path).status_code == 401
            assert client.get(path, headers=headers).status_code == 503
            assert client.get(path, headers=headers).status_code == expected
        with TestClient(create_app(settings)) as restarted:
            assert restarted.get(path, headers=headers).status_code == 503


def test_environment_validation(monkeypatch):
    monkeypatch.setenv("ALPHA_TOKEN", "alpha-test")
    monkeypatch.setenv("BETA_API_KEY", "beta-test")
    monkeypatch.setenv("MOCK_FAILURE_MODE", "none")
    assert Settings.from_env() == SETTINGS
    monkeypatch.setenv("MOCK_FAILURE_MODE", "invalid")
    with pytest.raises(ValueError, match="MOCK_FAILURE_MODE"):
        Settings.from_env()
    monkeypatch.setenv("MOCK_FAILURE_MODE", "none")
    monkeypatch.delenv("ALPHA_TOKEN")
    with pytest.raises(ValueError, match="ALPHA_TOKEN"):
        create_app()
