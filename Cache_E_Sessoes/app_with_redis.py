from flask import Flask, jsonify, session, redirect, url_for, request
from flask.sessions import SessionInterface # SessionDict removido
from werkzeug.datastructures import CallbackDict 
import time
import redis
import json
import os
from datetime import datetime, timedelta

class CustomSession(CallbackDict):
    def __init__(self, initial=None, sid=None, new=False, permanent=False):
        super().__init__(initial)
        self.sid = sid
        self.new = new
        self.modified = False
        self.permanent = permanent 


    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.modified = True


    def __delitem__(self, key):
        super().__delitem__(key)
        self.modified = True


class RedisSessionInterface(SessionInterface):
    """
    Interface de sessão Flask que armazena dados de sessão no Redis.
    Isso substitui o armazenamento padrão de sessão baseado em cookies,
    permitindo sessões mais robustas e centralizadas.
    """
    serializer = json 
    
    def __init__(self, host='localhost', port=6379, db=0, key_prefix='session:'):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.key_prefix = key_prefix
        self.session_class = CustomSession 

    def _generate_sid(self):
        return os.urandom(24).hex()
    

    def open_session(self, app, request):
        sid = request.cookies.get(app.config.get('SESSION_COOKIE_NAME', 'session')) 
        
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, new=True, permanent=app.permanent_session_lifetime)

        val = self.redis.get(self.key_prefix + sid)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(initial=data, sid=sid) 
        
        sid = self._generate_sid()
        return self.session_class(sid=sid, new=True, permanent=app.permanent_session_lifetime) 


    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session) # Flask agora pode calcular isso usando session.permanent

        session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')

        if not session: 
            if hasattr(session, 'sid') and session.sid:
                self.redis.delete(self.key_prefix + session.sid)
            response.delete_cookie(session_cookie_name, domain=domain, path=path)
            return

        if session.permanent:
            session_ttl_seconds = int(app.permanent_session_lifetime.total_seconds())
        else:
            session_ttl_seconds = 3600 


        if session.sid and session.modified: 
            val = self.serializer.dumps(dict(session)) 
            self.redis.setex(self.key_prefix + session.sid, session_ttl_seconds, val)
            
            response.set_cookie(
                session_cookie_name,
                session.sid,
                expires=expires, 
                httponly=httponly,
                domain=domain,
                path=path,
                secure=secure
            )

app = Flask(__name__)
app.secret_key = os.urandom(24) 
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS_HOST'] = 'localhost' 
app.config['SESSION_REDIS_PORT'] = 6379
app.config['SESSION_REDIS_DB'] = 0
app.config['SESSION_COOKIE_NAME'] = 'sessaoads' 

app.session_interface = RedisSessionInterface(
    host=app.config['SESSION_REDIS_HOST'],
    port=app.config['SESSION_REDIS_PORT'],
    db=app.config['SESSION_REDIS_DB']
)
app.permanent_session_lifetime = timedelta(minutes=30)

cache = redis.Redis(host='localhost', port=6379, db=1) 

DATABASE = {
    "1": {"username": "ana", "nome": "Ana Maria", "email": "alice@example.com", "idade": 30, "cidade": "Tauá"},
    "2": {"username": "brendan", "nome": "Brendan Souza", "email": "bruno@example.com", "idade": 25, "cidade": "Arneiroz"},
    "3": {"username": "clara", "nome": "Clara Oliveira", "email": "carla@example.com", "idade": 35, "cidade": "Parambu"},
    "4": {"username": "danael", "nome": "Daniel Santos", "email": "daniel@example.com", "idade": 40, "cidade": "Catarina"},
    "5": {"username": "emanuela", "nome": "Emanuela Carvalho", "email": "eva@example.com", "idade": 28, "cidade": "Boa Viagem"},
}

@app.route('/')
def index():
    if 'username' in session:
        return f'Olá, {session["username"]}! <a href="/logout">Sair</a> <br><a href="/pagina_protegida">Página Protegida</a> <br><a href="/dados_demorados/1">Acessar dados demorados (com cache)</a>'
    return 'Você não está logado. <a href="/login">Fazer Login</a> <br><a href="/dados_demorados/1">Acessar dados demorados (com cache)</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        print(f"Usuário {session['username']} já está logado. Redirecionando para a página inicial.")
        return redirect(url_for('index')) 

    if request.method == 'POST':
        username = request.form['username']
        
        if username in [user['username'] for user in DATABASE.values()]:
            session['username'] = username
            session['login_time'] = time.time()
            session.permanent = True 
            print(f"Usuário {username} logado. Sessão salva no Redis.")
            return redirect(url_for('index'))
        else:
            return 'Usuário inválido.'
    
    return '''
        <form method="post">
            <p><input type=text name=username></p>
            <p><input type=submit value=Login></p>
        </form>
    '''


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('login_time', None)
    return redirect(url_for('index'))


@app.route('/pagina_protegida')
def protected_page():
    if 'username' in session:
        login_dt = datetime.fromtimestamp(session['login_time'])
        return f"Bem-vindo à página protegida, {session['username']}! Você logou às {login_dt.strftime('%H:%M:%S de %d/%m/%Y')}"
    return redirect(url_for('login'))


@app.route('/dados_demorados/<item_id>')
def get_demorados_com_cache(item_id):
    start_time = time.time()
    cache_key = f"dados_cache:{item_id}" 

    cached_data = cache.get(cache_key)

    if cached_data:
        data = json.loads(cached_data)
        response_time = time.time() - start_time
        print(f"Dados do item {item_id} obtidos do CACHE em {response_time:.4f} segundos.")
        return jsonify(data)
    else:
        print(f"Buscando item {item_id} no 'banco de dados' (cache miss)...")
        time.sleep(2) 

        data = DATABASE.get(item_id)

        if data:
            cache.setex(cache_key, 60, json.dumps(data)) 
            response_time = time.time() - start_time
            print(f"Dados do item {item_id} obtidos do 'banco de dados' e CACHEADOS em {response_time:.2f} segundos.")
            return jsonify(data)
        else:
            response_time = time.time() - start_time
            print(f"Item {item_id} não encontrado. Tempo: {response_time:.2f} segundos (sem cache).")
            return jsonify({"erro": "Item não encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)