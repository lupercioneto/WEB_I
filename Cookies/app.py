# app.py
from flask import Flask, request, make_response

# Inicializa a aplicação Flask
app = Flask(__name__)

# Rota principal para uma mensagem de boas-vindas e links de navegação
@app.route('/')
def index():
    return """
    <h1>Bem-vindo à aplicação de demonstração de Cookies!</h1>
    <p>Este sistema simula operações básicas de gerenciamento de estado no lado do cliente.</p>
    <ul>
        <li><a href="/definir-cookie-sessao">Definir cookie de sessão</a></li>
        <li><a href="/definir-cookie-persistente">Definir cookie persistente (expira após 7 dias)</a></li>
        <li><a href="/ler-cookie">Ler o cookie armazenado</a></li>
        <li><a href="/remover-cookie">Remover cookie</a></li>
    </ul>
    """

# Rotas

@app.route('/definir-cookie-sessao')
def definir_cookie_sessao():
    
    resposta = make_response("Cookie de sessão 'usuario_logado' definido com sucesso.")
    resposta.set_cookie('usuario_logado', 'admin', httponly=True, secure=True)
    
    return resposta

@app.route('/definir-cookie-persistente')
def definir_cookie_persistente():

    resposta = make_response("Cookie persistente 'token_autenticacao' definido. Ele expira em 7 dias.")
    resposta.set_cookie('token_autenticacao', 'abc123DEF456', max_age=60*60*24*7, httponly=True, secure=True)
    
    return resposta


@app.route('/ler-cookie')
def ler_cookie():
    usuario = request.cookies.get('usuario_logado', 'Nenhum cookie de sessão encontrado.')
    token = request.cookies.get('token_autenticacao', 'Nenhum cookie persistente encontrado.')
    
    return f"""
    <h1>Cookies Atuais</h1>
    <p>Valor do cookie de sessão <strong>'usuario_logado'</strong>: <strong>{usuario}</strong></p>
    <p>Valor do cookie persistente <strong>'token_autenticacao'</strong>: <strong>{token}</strong></p>
    <p><a href="/">Voltar à Página Inicial</a></p>
    """


@app.route('/remover-cookie')
def remover_cookie():
    resposta = make_response("Cookies 'usuario_logado' e 'token_autenticacao' removidos com sucesso.")
    # Para remover um cookie, definimos seu valor como vazio e sua data de expiração no passado (expires=0).
    
    # O navegador, ao receber este Set-Cookie, entende que deve apagar o cookie.
    resposta.set_cookie('usuario_logado', '', expires=0)
    resposta.set_cookie('token_autenticacao', '', expires=0)
    return resposta


@app.route('/contador-visitas')
def contador_visitas():
    
    visitas = request.cookies.get('visitas_count')

    if visitas:
        try:
            contador = int(visitas) + 1
        except ValueError:
            contador = 1  
    else:
        contador = 1

    resposta = make_response(f"""
        <h1>Contador de Visitas</h1>
        <p>Você visitou esta página <strong>{contador}</strong> vezes.</p>
        <p><a href="/">Voltar à Página Inicial</a></p>
    """)

    # duração de um ano 
    um_ano = 60 * 60 * 24 * 365
    resposta.set_cookie('visitas_count', str(contador), max_age=um_ano, httponly=True, secure=True)

    return resposta


# Fim das Rotas

if __name__ == '__main__':
    app.run(debug=True)