from flask import Flask, jsonify
import time
import redis
import json

app = Flask(__name__)


cache = redis.Redis(host='localhost', port=6379, db=0)

DATABASE = {
    "1": {"nome": "Alice Silva", "email": "alice@example.com", "idade": 30, "cidade": "São Paulo"},
    "2": {"nome": "Bruno Costa", "email": "bruno@example.com", "idade": 25, "cidade": "Rio de Janeiro"},
    "3": {"nome": "Carla Dias", "email": "carla@example.com", "idade": 35, "cidade": "Belo Horizonte"},
    "4": {"nome": "Daniel Alves", "email": "daniel@example.com", "idade": 40, "cidade": "Curitiba"},
    "5": {"nome": "Eva Souza", "email": "eva@example.com", "idade": 28, "cidade": "Porto Alegre"},
}

@app.route('/usuarios_cache/<user_id>')
def get_user_with_cache(user_id):
    start_time = time.time()
    cache_key = f"user:{user_id}" 

    cached_data = cache.get(cache_key)

    if cached_data:
        
        user_data = json.loads(cached_data) 
        response_time = time.time() - start_time
        print(f"Dados do usuário {user_id} obtidos do CACHE em {response_time:.4f} segundos.")
        return jsonify(user_data)
    
    else:
        print(f"Buscando usuário {user_id} no 'banco de dados' (cache miss)...")
        
        time.sleep(2) 

        user_data = DATABASE.get(user_id)

        if user_data:
            cache.setex(cache_key, 60, json.dumps(user_data))         
            response_time = time.time() - start_time
            print(f"Dados do usuário {user_id} obtidos do 'banco de dados' e CACHEADOS em {response_time:.2f} segundos.")
            return jsonify(user_data)
        else:
            response_time = time.time() - start_time
            print(f"Usuário {user_id} não encontrado. Tempo: {response_time:.2f} segundos (sem cache).")
            return jsonify({"erro": "Usuário não encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001) 