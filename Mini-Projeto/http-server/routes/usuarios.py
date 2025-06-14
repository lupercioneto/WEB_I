import os
from urllib.parse import parse_qs

# Define o caminho para o arquivo que servirá como banco de dados.
CAMINHO_ARQUIVO = "usuarios.txt"

def carregar_usuarios():
    """Carrega os usuários do arquivo usuarios.txt."""
    if not os.path.exists(CAMINHO_ARQUIVO):
        return []
    with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
        linhas = f.readlines()
    usuarios = []
    for linha in linhas:
        if linha.strip(): # Ignora linhas em branco
            partes = linha.strip().split("|")
            usuarios.append({
                "id": int(partes[0]),
                "nome": partes[1],
                "email": partes[2],
                "telefone": partes[3],
            })
    return usuarios

def salvar_usuarios(usuarios):
    """Salva a lista de usuários no arquivo usuarios.txt."""
    with open(CAMINHO_ARQUIVO, "w", encoding="utf-8") as f:
        for u in usuarios:
            linha = f"{u['id']}|{u['nome']}|{u['email']}|{u['telefone']}\n"
            f.write(linha)

# --- Handlers do CRUD ---

def listar_usuarios(request, response):
    """Handler para exibir a lista de todos os usuários (Read)."""
    usuarios = carregar_usuarios()
    # Cria o corpo HTML dinamicamente com a lista de usuários
    html_body = "<h1>Lista de Usuários</h1>"
    html_body += '<a href="/usuarios/novo">Novo Usuário</a><br><br>'
    html_body += '<table border="1" style="border-collapse: collapse; width: 60%;"><tr><th style="padding: 8px;">ID</th><th style="padding: 8px;">Nome</th><th style="padding: 8px;">Ações</th></tr>'
    for u in usuarios:
        html_body += (
            f"<tr>"
            f'<td style="padding: 8px;">{u["id"]}</td>'
            f'<td style="padding: 8px;">{u["nome"]}</td>'
            f'<td style="padding: 8px;">'
            f'<a href="/usuarios/{u["id"]}">Detalhar</a> | '
            f'<a href="/usuarios/{u["id"]}/editar">Editar</a> | '
            f'<form method="POST" action="/usuarios/{u["id"]}/excluir" style="display:inline;">'
            f'<button type="submit">Excluir</button>'
            f'</form>'
            f"</td>"
            f"</tr>"
        )
    html_body += "</table>"
    response.send(200, html_body)

def novo_usuario(request, response):
    """Handler para exibir o formulário de criação de um novo usuário."""
    html_body = """
    <h1>Novo Usuário</h1>
    <form method="POST" action="/usuarios">
        <label for="nome">Nome:</label><br>
        <input type="text" id="nome" name="nome" required size="30"><br><br>
        <label for="email">Email:</label><br>
        <input type="email" id="email" name="email" required size="30"><br><br>
        <label for="telefone">Telefone:</label><br>
        <input type="text" id="telefone" name="telefone" size="30"><br><br>
        <button type="submit">Salvar</button>
    </form>
    <a href="/usuarios">Voltar para a lista</a>
    """
    response.send(200, html_body)

def criar_usuario(request, response):
    """Handler para processar a criação de um novo usuário (Create)."""
    dados = parse_qs(request.body)
    nome = dados.get('nome', [''])[0]
    email = dados.get('email', [''])[0]
    telefone = dados.get('telefone', [''])[0]

    usuarios = carregar_usuarios()
    novo_id = max([u['id'] for u in usuarios]) + 1 if usuarios else 1

    novo = {"id": novo_id, "nome": nome, "email": email, "telefone": telefone}
    usuarios.append(novo)
    salvar_usuarios(usuarios)
    
    response.redirect("/usuarios")

def detalhar_usuario(request, response):
    """Handler para exibir os detalhes de um usuário específico."""
    try:
        id_usuario = int(request.path.split('/')[2])
    except (IndexError, ValueError):
        return response.send(400, "ID de usuário inválido.")

    usuarios = carregar_usuarios()
    usuario = next((u for u in usuarios if u['id'] == id_usuario), None)

    if usuario:
        html_body = (
            f"<h1>Detalhes de {usuario['nome']}</h1>"
            f"<p><strong>ID:</strong> {usuario['id']}</p>"
            f"<p><strong>Email:</strong> {usuario['email']}</p>"
            f"<p><strong>Telefone:</strong> {usuario['telefone']}</p>"
            f'<br><a href="/usuarios">Voltar para a lista</a> | <a href="/usuarios/{usuario["id"]}/editar">Editar</a>'
        )
        response.send(200, html_body)
    else:
        response.send(404, "Usuário não encontrado.")

def editar_usuario(request, response):
    """Handler para exibir o formulário de edição de um usuário."""
    try:
        id_usuario = int(request.path.split('/')[2])
    except (IndexError, ValueError):
        return response.send(400, "ID de usuário inválido.")

    usuarios = carregar_usuarios()
    usuario = next((u for u in usuarios if u['id'] == id_usuario), None)

    if usuario:
        html_body = f"""
        <h1>Editar Usuário: {usuario['nome']}</h1>
        <form method="POST" action="/usuarios/{usuario['id']}/atualizar">
            <label for="nome">Nome:</label><br>
            <input type="text" id="nome" name="nome" value="{usuario['nome']}" required size="30"><br><br>
            <label for="email">Email:</label><br>
            <input type="email" id="email" name="email" value="{usuario['email']}" required size="30"><br><br>
            <label for="telefone">Telefone:</label><br>
            <input type="text" id="telefone" name="telefone" value="{usuario['telefone']}" size="30"><br><br>
            <button type="submit">Atualizar</button>
        </form>
        <a href="/usuarios">Cancelar</a>
        """
        response.send(200, html_body)
    else:
        response.send(404, "Usuário não encontrado.")

def atualizar_usuario(request, response):
    """Handler para processar a atualização de um usuário (Update)."""
    try:
        id_usuario = int(request.path.split('/')[2])
    except (IndexError, ValueError):
        return response.send(400, "ID de usuário inválido.")

    dados = parse_qs(request.body)
    usuarios = carregar_usuarios()
    
    usuario_encontrado = False
    for u in usuarios:
        if u['id'] == id_usuario:
            u['nome'] = dados.get('nome', [u['nome']])[0]
            u['email'] = dados.get('email', [u['email']])[0]
            u['telefone'] = dados.get('telefone', [u['telefone']])[0]
            usuario_encontrado = True
            break
    
    if usuario_encontrado:
        salvar_usuarios(usuarios)
        response.redirect("/usuarios")
    else:
        response.send(404, "Usuário não encontrado para atualizar.")

def excluir_usuario(request, response):
    """Handler para processar a exclusão de um usuário (Delete)."""
    try:
        id_usuario = int(request.path.split('/')[2])
    except (IndexError, ValueError):
        return response.send(400, "ID de usuário inválido.")
        
    usuarios = carregar_usuarios()
    usuarios_restantes = [u for u in usuarios if u['id'] != id_usuario]

    if len(usuarios_restantes) < len(usuarios):
        salvar_usuarios(usuarios_restantes)
        response.redirect("/usuarios")
    else:
        response.send(404, "Usuário não encontrado para excluir.")