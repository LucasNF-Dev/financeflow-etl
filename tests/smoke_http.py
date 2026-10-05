"""Smoke HTTP real; execute com o servidor em modo normal e ambiente exportado."""

import json
import os
import urllib.request
import urllib.error

base = os.environ.get('MOCK_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
def get(path, headers=None):
    with urllib.request.urlopen(urllib.request.Request(base+path, headers=headers or {}), timeout=3) as response:
        assert response.status == 200
        return json.load(response)

assert get('/health') == {'status':'ok'}
alpha_headers = {'Authorization': 'Bearer ' + os.environ['ALPHA_TOKEN']}
beta_headers = {'X-API-Key': os.environ['BETA_API_KEY']}
alpha = []
for page in range(1,4):
    body = get(f'/alpha/transactions?page={page}&page_size=2', alpha_headers)
    assert body['next_page'] == (page + 1 if page < 3 else None)
    alpha += body['data']
beta = []
for page in range(1,3):
    body = get(f'/beta/lancamentos?pagina={page}&limite=2', beta_headers)
    assert body['pagina'] == page and body['total_paginas'] == 2
    beta += body['lancamentos']
assert [r['id'] for r in alpha] == ['A-1','A-2','A-2','A-3','A-X']
assert [r['codigo'] for r in beta] == ['B-1','B-2','B-3']
assert alpha[1] == alpha[2] and alpha[4]['amount'] == 'abc'
assert get('/alpha/transactions?page=4', alpha_headers) == {'data':[], 'next_page':None}
assert get('/beta/lancamentos?pagina=3', beta_headers) == {'lancamentos':[], 'pagina':3, 'total_paginas':2}
for path, headers in [('/alpha/transactions',{}),('/alpha/transactions',{'Authorization':'Bearer wrong'}),('/beta/lancamentos',{}),('/beta/lancamentos',{'X-API-Key':'wrong'})]:
    try:
        get(path, headers)
    except urllib.error.HTTPError as error:
        assert error.code == 401
    else:
        raise AssertionError('Credencial inválida foi aceita')
print('HTTP OK: health, 5 páginas, 8 brutos, fim e 4 respostas 401')
print('Alpha:', json.dumps(get('/alpha/transactions?page_size=1', alpha_headers), ensure_ascii=False))
print('Beta:', json.dumps(get('/beta/lancamentos?limite=1', beta_headers), ensure_ascii=False))
