# Flask Multi-Auth Demo

## O que está implementado
- JWT (Bearer) — gera um JWT assinado; verificação em header `Authorization: Bearer <token>` ou cookie `access_token`.
- Token Authentication (opaque token) — gera token aleatório armazenado server-side; use `Authorization: Token <token>`.
- HTTP Basic Authentication — validação via header `Authorization: Basic <base64(user:pass)>`.

## Como rodar
1. Crie um virtualenv e ative:
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
2. Instale requisitos:
   pip install -r requirements.txt
3. Rode:
   python app.py
4. Acesse http://localhost:5000

## Notas e limitações
- Armazenamento em memória: reiniciar o servidor limpa tokens.
- Em produção **use HTTPS**, altere chaves secretas e use um banco de dados.
- JWT tem expiração curta; a revogação de JWT foi simplificada: o cliente deve descartar o token.

## Pontos levantados na pesquisa (roadmap.sh)
- JWT: bom para APIs sem estado; prós: stateless, escalável; contras: revogação complexa, tokens longos.
- Token (opaque): simples de revogar (server-side), controla sessão; prós: fácil revogação; contras: precisa de armazenamento server-side.
- Basic Auth: muito simples, mas inseguro sem HTTPS; prós: compatível com ferramentas; contras: envia credenciais em cada requisição.
