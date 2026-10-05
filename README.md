# FinanceFlow ETL

Projeto em desenvolvimento. A etapa 1 está concluída; as etapas 2 a 6 estão pendentes.
Esta entrega implementa somente a etapa 1 do
[guia](FinanceFlow_Guia_Implementacao.md): pacote instalável e duas APIs financeiras
sintéticas em um serviço FastAPI. Todos os dados e tokens são fictícios.
Coletores, transformação, banco, indicadores, Airflow e dashboard ficam para etapas futuras.

## Executar localmente

Use Python 3.12 ou superior. O container usa Python 3.12.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-build-isolation --no-deps -e .
cp .env.example .env
set -a
source .env
set +a
python -m uvicorn mock_api.main:create_app --factory --host 127.0.0.1 --port 8000
```

As variáveis `ALPHA_TOKEN` e `BETA_API_KEY` são obrigatórias e não podem ser vazias.
O Python não carrega `.env` automaticamente; os comandos acima exportam seus valores.
Pare o servidor com Ctrl+C. Documentação interativa: http://localhost:8000/docs.

Em outro terminal, na pasta do projeto:

```bash
set -a
source .env
set +a
curl --fail-with-body http://localhost:8000/health
curl --fail-with-body -H "Authorization: Bearer $ALPHA_TOKEN" 'http://localhost:8000/alpha/transactions?page=1&page_size=2'
curl --fail-with-body -H "X-API-Key: $BETA_API_KEY" 'http://localhost:8000/beta/lancamentos?pagina=1&limite=2'
curl -i -H 'Authorization: Bearer wrong' http://localhost:8000/alpha/transactions
.venv/bin/python tests/smoke_http.py
```

## Docker Compose

Com Docker e o plugin Compose instalados:

```bash
cp .env.example .env
docker compose up -d --build mock-api
docker compose ps
docker compose logs mock-api
docker compose run --rm mock-api python -m pytest -q -p no:cacheprovider
docker compose down
```

Os comandos `curl` acima também consultam o container. A imagem contém os testes
e as mesmas dependências fixadas em `requirements.lock`, inclusive ferramentas de
teste e build, para esta demonstração pequena. O serviço roda sem usuário root e
expõe a porta somente na interface local. `.env` não entra na imagem.

## Contratos e exemplos

Uma API oferece operações acessíveis por HTTP. Aqui um `GET` devolve dados em JSON.
Headers carregam metadados da requisição, como a credencial. Query parameters,
depois de `?` na URL, escolhem a página e a quantidade de registros.

Alpha usa `Authorization: Bearer <ALPHA_TOKEN>`; Beta usa `X-API-Key: <BETA_API_KEY>`.
Credenciais ausentes, erradas ou enviadas no header da outra fonte retornam 401.
`/health` é público e retorna `{"status":"ok"}`. Parâmetros de paginação devem
ser inteiros positivos; valores inválidos retornam 422.

Alpha, `GET /alpha/transactions?page=1&page_size=1`:

```json
{
  "data": [{
    "id": "A-1", "company_id": "C1", "description": "Serviço de setembro",
    "amount": "3000.00", "category": "SERVICOS",
    "competence_date": "2026-09-30", "payment_date": "2026-10-02", "status": "PAID"
  }],
  "next_page": 2
}
```

Beta, `GET /beta/lancamentos?pagina=1&limite=1`:

```json
{
  "lancamentos": [{
    "codigo": "B-1", "empresa": "C1", "historico": "Venda de outubro",
    "valor": "2500,00", "tipo": "RECEITA", "categoria": "SERVICOS",
    "competencia": "02/10/2026", "pagamento": "03/10/2026", "situacao": "PAGO"
  }],
  "pagina": 1,
  "total_paginas": 3
}
```

Os schemas diferentes simulam sistemas independentes: Alpha usa nomes em inglês,
datas ISO e sinal negativo para despesas; Beta usa nomes em português, datas
brasileiras, vírgula decimal e um campo de tipo. Dinheiro permanece como string.

A ordenação por ID é estável. Com tamanho 2 (padrão), Alpha tem três páginas,
com 2, 2 e 1 registros; `next_page=null` encerra. Beta tem duas páginas, com 2 e 1
registros; `pagina == total_paginas` encerra. Uma página além do fim retorna lista
vazia; Alpha mantém `next_page=null` e Beta mantém o total de páginas.

São 5 registros Alpha (`A-1`, `A-2`, `A-2`, `A-3`, `A-X`) e 3 Beta (`B-1`, `B-2`,
`B-3`): 8 brutos. A duplicata de A-2 é idêntica; A-X tem `amount="abc"`.
O mock preserva ambos para os testes de qualidade de etapas futuras. O lançamento
cancelado B-3 também é preservado. A conciliação entre fontes está fora do MVP;
nas etapas futuras uma operação presente nos dois ERPs será contada duas vezes.

## Falhas controladas

`MOCK_FAILURE_MODE=none` é o modo normal. Use `once` para devolver 503 na primeira
requisição autenticada à página 2 de cada ERP; a próxima tentativa funciona.
Use `always` para devolver 503 em toda requisição autenticada à página 2.
Use tamanho 2 para que a página 2 contenha dados em ambas as fontes.

Localmente, pare o processo e reinicie, por exemplo:

```bash
MOCK_FAILURE_MODE=once python -m uvicorn mock_api.main:create_app --factory --host 127.0.0.1 --port 8000
```

No Compose, altere `MOCK_FAILURE_MODE` no `.env` e execute:

```bash
docker compose up -d --force-recreate mock-api
```

O estado de `once` vive na memória de cada processo. Reiniciar o processo ou
recriar o container reinicia o cenário. Use um único worker nesta demonstração.
Para voltar ao contrato normal, restaure `none` e reinicie. Retries HTTP e coleta
completa serão implementados somente na etapa 2.

## Organização e testes

- `src/financeflow/`: pacote e validação das variáveis de ambiente.
- `mock_api/main.py`: fábrica FastAPI, autenticação, paginação e falhas sintéticas.
- `mock_api/fixtures/`: JSONs determinísticos incluídos no pacote instalado.
- `tests/test_mock_api.py`: contratos, conteúdo dos 8 registros, autenticação,
  encerramento, parâmetros inválidos, reinício e falhas controladas.
- `pyproject.toml`: metadados; `requirements.lock`: versões diretas e transitivas.
- `Dockerfile` e `compose.yaml`: somente o serviço `mock-api` nesta etapa.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

As expectativas dos testes são escritas independentemente dos JSONs de produção.
Consulte [docs/validation.md](docs/validation.md) para os resultados e impedimentos
observados nesta entrega. Referência consultada para a versão fixada:
[notas oficiais do FastAPI 0.115.12](https://fastapi.tiangolo.com/release-notes/#011512).
