from server import Server
from routes.usuarios import *

app = Server()

# --- Registro das Rotas do CRUD de Usuários ---
app.route("/usuarios")(listar_usuarios)

app.route("/usuarios/novo")(novo_usuario)

app.route("/usuarios", methods=["POST"])(criar_usuario)

app.route("/usuarios/<id>")(detalhar_usuario)

app.route("/usuarios/<id>/editar")(editar_usuario)

app.route("/usuarios/<id>/atualizar", methods=["POST"])(atualizar_usuario)

app.route("/usuarios/<id>/excluir", methods=["POST"])(excluir_usuario)

if __name__ == "__main__":
    app.start()