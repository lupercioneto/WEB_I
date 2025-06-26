from flask import Flask, jsonify, session, redirect, url_for, request
import time
import json
import os 

app = Flask(__name__)
app.secret_key = os.urandom(24) 

DATABASE = {
    "1": {"username": "alice", "nome": "Alice Silva", "email": "alice@example.com", "idade": 30, "cidade": "Tauá"},
    "2": {"username": "bruno", "nome": "Bruno Costa", "email": "bruno@example.com", "idade": 25, "cidade": "Arneiroz"},
}


@app.route('/')
def index():
    if 'username' in session:
        return f'Olá, {session["username"]}! <a href="/logout">Sair</a> <br><a href="/pagina_protegida">Página Protegida</a>'
    return 'Você não está logado. <a href="/login">Fazer Login</a>'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # Simula uma autenticação
        if username in [user['username'] for user in DATABASE.values()]:
            session['username'] = username
            session['login_time'] = time.time()
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
        return f"Bem-vindo à página protegida, {session['username']}! Você logou às {time.ctime(session['login_time'])}"
    return redirect(url_for('login'))


@app.route('/dados_demorados/<item_id>')
def get_demorados_sem_cache(item_id):
    start_time = time.time()
    print(f"Buscando item {item_id} no 'banco de dados' (demorado)...")
    
    time.sleep(2) 

    data = DATABASE.get(item_id)

    if data:
        response_time = time.time() - start_time
        print(f"Requisição para item {item_id} concluída em {response_time:.2f} segundos (sem cache).")
        return jsonify(data)
    else:
        response_time = time.time() - start_time
        print(f"Item {item_id} não encontrado. Tempo: {response_time:.2f} segundos (sem cache).")
        return jsonify({"erro": "Item não encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)