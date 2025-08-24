# app.py (versão revisada: usa users.json, cria usuários para teste, lista usuários)
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, abort
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import secrets
import base64
import json
import os

# CONFIG
SECRET_KEY = "change_this_secret_key_for_prod"  # troque em produção
JWT_SECRET = "change_this_jwt_secret_for_prod"
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 300  # 5 minutos (apenas demo)
USERS_FILE = "users.json"

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


# ----------------- Persistence helpers (users.json) -----------------
def load_users_from_file():
    """Retorna dicionário: username -> {password_hash, full_name (opt)}"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # aceitaremos tanto lista de objetos quanto dicionário já formatado
    users_dict = {}
    if isinstance(data, list):
        for entry in data:
            username = entry.get("username")
            # se for senha em texto, convert para hash agora (conveniência)
            pwd = entry.get("password") or entry.get("password_hash")
            if username and pwd:
                # detecta se parece hash (werkzeug hashes normalmente começam com 'pbkdf2:sha256:')
                if pwd.startswith("pbkdf2:") or pwd.startswith("scrypt:") or pwd.startswith("argon2"):
                    pwd_hash = pwd
                else:
                    pwd_hash = generate_password_hash(pwd)
                users_dict[username] = {
                    "password_hash": pwd_hash,
                    "full_name": entry.get("full_name", "")
                }
    elif isinstance(data, dict):
        # assume formato já mapa username -> {password_hash, full_name}
        users_dict = data
    return users_dict


def save_users_to_file(users_dict):
    """Salva dicionário como lista de objetos (mais legível)."""
    out = []
    for username, info in users_dict.items():
        out.append({
            "username": username,
            "password_hash": info.get("password_hash"),
            "full_name": info.get("full_name", "")
        })
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=4, ensure_ascii=False)


# Carrega usuários em memória (estrutura: username -> {...})
users = load_users_from_file()


# ----------------- In-memory token store (opaque tokens) -----------------
api_tokens = {}  # token_str -> {username, expires_at}


# ----------------- Auth helpers -----------------
def create_jwt(username):
    payload = {
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT >=2.0 returns a str, older returns bytes — normalize to str:
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def verify_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('sub')
    except Exception:
        return None


def create_opaque_token(username):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    api_tokens[token] = {'username': username, 'expires_at': expires_at}
    return token


def verify_opaque_token(token):
    data = api_tokens.get(token)
    if not data:
        return None
    if data['expires_at'] < datetime.utcnow():
        del api_tokens[token]
        return None
    return data['username']


def verify_basic_auth(header_value):
    """
    header_value ex: "Basic base64(user:pass)"
    Retorna username se ok, None se inválido.
    """
    try:
        if not header_value.startswith('Basic '):
            return None
        b64 = header_value.split(' ', 1)[1]
        decoded = base64.b64decode(b64).decode('utf-8')
        username, password = decoded.split(':', 1)
        user = users.get(username)
        if user and check_password_hash(user['password_hash'], password):
            return username
    except Exception:
        return None
    return None


# ----------------- Routes -----------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login page where user picks method: jwt | token | basic
    if request.method == 'GET':
        return render_template('login.html')

    method = request.form.get('method')
    username = request.form.get('username')
    password = request.form.get('password')

    user = users.get(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return render_template('login.html', error='Credenciais inválidas')

    if method == 'jwt':
        token = create_jwt(username)
        resp = make_response(render_template('token_result.html', token=token, method='JWT'))
        # atenção: cookie HttpOnly usado só pra dev; em produção use HTTPS e secure cookies
        resp.set_cookie('access_token', token, httponly=True)
        return resp

    elif method == 'token':
        token = create_opaque_token(username)
        return render_template('token_result.html', token=token, method='Opaque Token')

    elif method == 'basic':
        # Basic Auth normalmente é enviada pelo browser/curl; apenas instruímos
        return render_template('token_result.html', token=None, method='Basic', username=username)

    else:
        return render_template('login.html', error='Método inválido')


@app.route('/protected')
def protected():
    # Checa múltiplos métodos de autenticação
    auth_header = request.headers.get('Authorization', '')

    # 1) Bearer JWT
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        user = verify_jwt(token)
        if user:
            return render_template('protected.html', auth_method='JWT', user=user)
        else:
            return ('Invalid JWT', 401)

    # 2) Opaque Token (usamos prefixo "Token ")
    if auth_header.startswith('Token '):
        token = auth_header.split(' ', 1)[1]
        user = verify_opaque_token(token)
        if user:
            return render_template('protected.html', auth_method='Token', user=user)
        else:
            return ('Invalid Token', 401)

    # 3) Basic Auth
    if auth_header.startswith('Basic '):
        user = verify_basic_auth(auth_header)
        if user:
            return render_template('protected.html', auth_method='Basic', user=user)
        else:
            resp = make_response('Could not verify', 401)
            resp.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
            return resp

    # 4) Cookie JWT fallback
    token_cookie = request.cookies.get('access_token')
    if token_cookie:
        user = verify_jwt(token_cookie)
        if user:
            return render_template('protected.html', auth_method='JWT (cookie)', user=user)

    return ("""
401 Unauthorized. Esta rota aceita três métodos:
- JWT: Authorization: Bearer <token>
- Token: Authorization: Token <token>
- Basic: Authorization: Basic <base64(user:pass)> (ou use curl -u user:pass)

Tente novamente com as credenciais.
""", 401)


@app.route('/logout', methods=['GET'])
def logout():
    # Para tokens opacos, podemos remover do store se o usuário enviar o token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        token = auth_header.split(' ', 1)[1]
        api_tokens.pop(token, None)
        return 'Token revoked (server-side) \n'

    # Para JWT: instruímos o cliente a descartar o token (cookie pode ser apagado)
    resp = make_response('Logged out (discard JWT on client).')
    resp.set_cookie('access_token', '', expires=0)
    return resp


# ----------------- Utility endpoints para testar localmente -----------------
@app.route('/create-user', methods=['POST'])
def create_user():
    """
    Cria usuário para facilitar testes. Exemplo JSON body:
    { "username": "test", "password": "pass", "full_name": "Test User" }
    """
    if not request.is_json:
        return jsonify({"error": "Envie JSON"}), 400
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name", "")

    if not username or not password:
        return jsonify({"error": "username e password são obrigatórios"}), 400

    if username in users:
        return jsonify({"error": "Usuário já existe"}), 409

    pwd_hash = generate_password_hash(password)
    users[username] = {"password_hash": pwd_hash, "full_name": full_name}
    save_users_to_file(users)
    return jsonify({"ok": True, "username": username}), 201


@app.route('/list-users', methods=['GET'])
def list_users():
    """Retorna apenas lista de usernames (útil para teste)."""
    return jsonify(sorted(list(users.keys())))


@app.route('/reload-users', methods=['POST'])
def reload_users():
    """Recarrega users.json para memória (útil enquanto edita o arquivo manualmente)."""
    global users
    users = load_users_from_file()
    return jsonify({"ok": True, "loaded": len(users)})


if __name__ == '__main__':
    app.run(debug=True)
