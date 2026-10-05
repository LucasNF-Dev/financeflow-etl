# Validação da etapa 1

Entrega em 4 de outubro de 2026. Guia original preservado; nenhum `AGENTS.md`
encontrado na pasta ou nos diretórios ancestrais consultados.

## Resultados observados

- Python local: 3.14.7; instalação editável do pacote concluída.
- `.venv/bin/python -m pytest -q`: **25 passed** em 0,23 s.
  Cobertura: paginação completa com tamanhos 1, 2, 3 e 8; schemas; valores, datas
  e estados dos 8 registros; duplicata idêntica; valor inválido preservado;
  encerramento; autenticação; parâmetros inválidos; health; comparação de
  respostas entre instâncias novas; modos 503 e reinício de seu estado.
- `.venv/bin/python -m pip check`: **No broken requirements found**.
- Wheel construído e instalado em `/tmp/financeflow-installed`, importado fora da
  pasta do projeto. Ambos os pacotes e os dois JSONs estão presentes, e a fábrica
  da aplicação inicializa corretamente.
- Uvicorn executado em `127.0.0.1:8000`, com credenciais fictícias.
  Smoke HTTP real: health, três páginas Alpha, duas Beta, 8 registros,
  páginas além do fim e quatro respostas 401. Exemplos de ambos os ERPs
  consultados por HTTP. Após reiniciar o processo, o smoke salvo em
  `tests/smoke_http.py` passou novamente com os mesmos registros e exemplos.
  O servidor foi encerrado após a validação.

O pytest emitiu 94 avisos de depreciação de dependências: alias `BlockingPortal`
do AnyIO no Starlette e `asyncio.iscoroutinefunction` no FastAPI/Python 3.14.
Não houve falha de teste; os avisos não foram suprimidos.

## Comandos executados

Além da criação da venv e instalação das versões fixadas:

```bash
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
.venv/bin/python -m pip wheel --no-build-isolation --no-deps --wheel-dir /tmp/financeflow-wheel .
.venv/bin/python -m pip install --no-deps --target /tmp/financeflow-installed /tmp/financeflow-wheel/financeflow-0.1.0-py3-none-any.whl
ALPHA_TOKEN=alpha-demo-token BETA_API_KEY=beta-demo-key .venv/bin/python -m uvicorn mock_api.main:create_app --factory --host 127.0.0.1 --port 8000
ALPHA_TOKEN=alpha-demo-token BETA_API_KEY=beta-demo-key .venv/bin/python tests/smoke_http.py
```

## Impedimentos e limites

O sandbox falhou na resolução de `pypi.org`, bloqueou a abertura da porta local e
deixou o TestClient sem progresso. Instalação, testes e HTTP foram executados com
permissão fora do sandbox; a execução de testes bloqueada foi interrompida.

`docker` não está instalado (`command -v docker` não retornou executável).
Não foram executados build da imagem, Compose, healthcheck do container ou testes
em Python 3.12. Os comandos correspondentes estão no README para validação local.
A repetibilidade das respostas foi testada entre instâncias novas da aplicação.

`git status --short` retornou `fatal: not a git repository`; o diretório `.git`
disponível não contém um repositório utilizável. Não foi possível gerar diff,
stage ou commit. Os arquivos estão preparados no diretório para revisão.
Nenhum recurso da etapa 2 foi implementado.
