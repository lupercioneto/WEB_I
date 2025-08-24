from flask import Flask, jsonify, request, send_from_directory
from models import db, RefreshToken
import jwt
import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "mySecretKey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Função para gerar o token de acesso
def gerar_access_token(user):
    payload = {
        "userId": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

# Função para gerar e salvar o refresh token
def gerar_refresh_token(user):
    payload = {
        "userId": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    novo = RefreshToken(
        token=token,
        user_id=user["id"],
        created_at=datetime.datetime.utcnow()
    )
    db.session.add(novo)
    db.session.commit()

    return token

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.before_request
def cria_banco():
    db.create_all()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if data["username"] == "john" and data["password"] == "1234":
        user = {"id": 1, "username": "john", "role": "admin"}
        access_token = gerar_access_token(user)
        refresh_token = gerar_refresh_token(user)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    return jsonify({"erro": "Credenciais inválidas"}), 401

@app.route("/protegido", methods=["GET"])
def protegido():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"erro": "Token ausente"}), 401

    token = auth_header.replace("Bearer ", "")
    try:
        decoded = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return jsonify({"mensagem": "Acesso permitido!", "usuario": decoded})
    except jwt.ExpiredSignatureError:
        return jsonify({"erro": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"erro": "Token inválido"}), 401

@app.route("/refresh-token", methods=["POST"])
def refresh():
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"erro": "Token ausente"}), 401

    encontrado = RefreshToken.query.filter_by(token=refresh_token).first()
    if not encontrado:
        return jsonify({"erro": "Token inválido ou revogado"}), 403

    try:
        decoded = jwt.decode(refresh_token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = {
            "id": decoded["userId"],
            "username": decoded["username"],
            "role": decoded["role"]
        }
        novo_token = gerar_access_token(user)
        return jsonify({"access_token": novo_token})
    except jwt.ExpiredSignatureError:
        return jsonify({"erro": "Refresh token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"erro": "Token inválido"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    token_db = RefreshToken.query.filter_by(token=refresh_token).first()
    if token_db:
        db.session.delete(token_db)
        db.session.commit()

    return jsonify({"mensagem": "Logout realizado com sucesso."})


if __name__ == "__main__":
	with app.app_context():
		db.create_all()
app.run(debug=True)
