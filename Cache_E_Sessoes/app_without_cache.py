from flask import Flask, jsonify
import time
import json # Para simular dados complexos

app = Flask(__name__)

# Simula um "banco de dados" de usuários - dados estáticos por simplicidade
DATABASE = {
    "1": {"nome": "Alice Silva", "email": "alice@example.com", "idade": 30, "cidade": "São Paulo"},
    "2": {"nome": "Bruno Costa", "email": "bruno@example.com", "idade": 25, "cidade": "Rio de Janeiro"},
    "3": {"nome": "Carla Dias", "email": "carla@example.com", "idade": 35, "cidade": "Belo Horizonte"},
    "4": {"nome": "Daniel Alves", "email": "daniel@example.com", "idade": 40, "cidade": "Curitiba"},
    "5": {"nome": "Eva Souza", "email": "eva@example.com", "idade": 28, "cidade": "Porto Alegre"},
}

# Rota para obter detalhes de um usuário sem cache
@app.route('/usuarios/<user_id>')
def get_user_without_cache(user_id):
    start_time = time.time() # Início da medição de tempo

    print(f"Buscando usuário {user_id} no 'banco de dados' (sem cache)...")
    
    # Simula uma operação demorada no banco de dados
    time.sleep(2) # Espera 2 segundos para simular a lentidão

    user_data = DATABASE.get(user_id)

    if user_data:
        response_time = time.time() - start_time
        print(f"Requisição para usuário {user_id} concluída em {response_time:.2f} segundos (sem cache).")
        return jsonify(user_data)
    else:
        response_time = time.time() - start_time
        print(f"Usuário {user_id} não encontrado. Tempo: {response_time:.2f} segundos (sem cache).")
        return jsonify({"erro": "Usuário não encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)