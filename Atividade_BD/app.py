import os
from typing import Optional, Tuple, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash

import bcrypt
import psycopg
from psycopg.rows import dict_row
import re


# Tenta usar pool; se não houver, cai para conexão direta
try:
    from psycopg_pool import ConnectionPool  # type: ignore
    HAS_POOL = True
except Exception:
    HAS_POOL = False

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ----------------------------
# Conexão / Pool
# ----------------------------
if HAS_POOL:
    pool = ConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=5,
        timeout=10,
        kwargs={"autocommit": False},
    )

    def _conn():
        return pool.connection()

else:
    # Fallback sem pool
    def _conn():
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

# Helpers de DB
def db_query(sql: str, params: Optional[Tuple] = None) -> List[dict]:
    with _conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def db_execute(sql: str, params: Optional[Tuple] = None, returning: bool = False):
    with _conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall() if returning else None
        conn.commit()
    return rows

# ----------------------------
# Utilidades de senha
# ----------------------------
def hash_password(plain: str) -> str:
    # bcrypt gera bytes ASCII (ex.: $2b$12$...), convertemos para str para salvar em VARCHAR
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# ----------------------------
# Endpoints
# ----------------------------
@app.get("/health")
def health():
    try:
        one = db_query("SELECT 1 AS ok;")[0]["ok"]
        return jsonify({"status": "ok", "db": one, "pool": HAS_POOL}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.get("/db/version")
def db_version():
    try:
        v = db_query("SELECT version();")[0]["version"]
        return jsonify({"version": v}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Users CRUD (tabela public.usuarios) ----

@app.get("/users")
def list_users():
    try:
        rows = db_query("SELECT id, nome, email FROM public.usuarios ORDER BY id ASC;")
        return jsonify({"data": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/users/<int:user_id>")
def get_user(user_id: int):
    try:
        rows = db_query(
            "SELECT id, nome, email FROM public.usuarios WHERE id = %s;",
            (user_id,),
        )
        if not rows:
            return jsonify({"error": "usuário não encontrado"}), 404
        return jsonify({"data": rows[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/users")
def create_user():
    try:
        payload = request.get_json(silent=True) or {}
        nome = payload.get("nome")
        email = payload.get("email")
        senha = payload.get("senha")

        if not all([nome, email, senha]):
            return jsonify({"error": "nome, email e senha são obrigatórios"}), 400

        senha_hash = hash_password(senha)

        row = db_execute(
            """
            INSERT INTO public.usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
            RETURNING id, nome, email;
            """,
            (nome, email, senha_hash),
            returning=True,
        )
        return jsonify({"data": row[0]}), 201

    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "email já cadastrado"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.put("/users/<int:user_id>")
def update_user(user_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        nome = payload.get("nome")
        email = payload.get("email")
        senha = payload.get("senha")

        sets = []
        params: List = []

        if nome:
            sets.append("nome = %s")
            params.append(nome)
        if email:
            sets.append("email = %s")
            params.append(email)
        if senha:
            sets.append("senha = %s")
            params.append(hash_password(senha))

        if not sets:
            return jsonify({"error": "nenhum campo para atualizar"}), 400

        params.append(user_id)

        sql = f"""
            UPDATE public.usuarios
               SET {', '.join(sets)}
             WHERE id = %s
         RETURNING id, nome, email;
        """

        rows = db_execute(sql, tuple(params), returning=True)
        if not rows:
            return jsonify({"error": "usuário não encontrado"}), 404

        return jsonify({"data": rows[0]}), 200

    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "email já cadastrado"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    try:
        rows = db_execute(
            "DELETE FROM public.usuarios WHERE id = %s RETURNING id;",
            (user_id,),
            returning=True,
        )
        if not rows:
            return jsonify({"error": "usuário não encontrado"}), 404
        # 204 No Content também seria aceitável; aqui retornamos um JSON simples
        return jsonify({"deleted": rows[0]["id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------- FORMULÁRIOS HTML ---------

@app.get("/users/new")
def users_new_form():
    """Renderiza o formulário de cadastro (HTML)."""
    return render_template("users_new.html")

@app.post("/users/form")
def users_create_from_form():
    """
    Recebe POST de <form> (x-www-form-urlencoded).
    Faz validação, hash (bcrypt) e INSERT com parâmetros.
    """
    try:
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""

        # Validações simples de servidor
        if not nome or not email or not senha:
            flash("Preencha nome, email e senha.", "error")
            return redirect(url_for("users_new_form"))

        if "@" not in email:
            flash("Email inválido.", "error")
            return redirect(url_for("users_new_form"))

        senha_hash = hash_password(senha)

        row = db_execute(
            """
            INSERT INTO public.usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
            RETURNING id, nome, email;
            """,
            (nome, email, senha_hash),
            returning=True,
        )
        flash(f"Usuário {row[0]['email']} criado com sucesso!", "success")
        return redirect(url_for("users_page"))

    except psycopg.errors.UniqueViolation:
        flash("Email já cadastrado.", "error")
        return redirect(url_for("users_new_form"))
    except Exception as e:
        flash(f"Erro inesperado: {e}", "error")
        return redirect(url_for("users_new_form"))

@app.get("/users/page")
def users_page():
    """
    Lista usuários em HTML. Suporta busca (?q=...) com ILIKE parametrizado.
    Também suporta paginação simples (?limit=&offset=).
    """
    try:
        q = (request.args.get("q") or "").strip()
        try:
            limit = max(1, min(int(request.args.get("limit", 20)), 100))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.args.get("offset", 0)))
        except ValueError:
            offset = 0

        if q:
            like = f"%{q}%"
            rows = db_query(
                """
                SELECT id, nome, email
                  FROM public.usuarios
                 WHERE nome ILIKE %s OR email ILIKE %s
                 ORDER BY id ASC
                 LIMIT %s OFFSET %s;
                """,
                (like, like, limit, offset),
            )
        else:
            rows = db_query(
                """
                SELECT id, nome, email
                  FROM public.usuarios
                 ORDER BY id ASC
                 LIMIT %s OFFSET %s;
                """,
                (limit, offset),
            )

        next_offset = offset + limit
        prev_offset = max(0, offset - limit)

        return render_template(
            "users_page.html", 
            users=rows, 
            q=q, 
            limit=limit, 
            offset=offset,
            prev_offset=prev_offset,
            next_offset=next_offset)
    except Exception as e:
        # Para debug em aula, mostramos o erro; em produção, logue e mostre página amigável
        return f"<h3>Erro ao listar usuários:</h3><pre>{e}</pre>", 500


@app.get("/users/<int:user_id>/edit")
def user_edit_form(user_id: int):
    rows = db_query("SELECT id, nome, email FROM public.usuarios WHERE id = %s;", (user_id,))
    if not rows:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("list_users"))
    user = rows[0]
    return render_template("users_edit.html", user=user)

@app.post("/users/<int:user_id>/edit")
def user_edit_submit(user_id: int):
    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    senha = request.form.get("senha") or ""

    # Validação
    erros = []
    if not (2 <= len(nome) <= 120):
        erros.append("Nome deve ter entre 2 e 120 caracteres.")
    if not EMAIL_REGEX.match(email):
        erros.append("Email inválido.")
    if senha and len(senha) < 6:
        erros.append("Senha deve ter pelo menos 6 caracteres.")

    if erros:
        for e in erros:
            flash(e, "error")
        return redirect(url_for("user_edit_form", user_id=user_id))

    # Montar update
    sets = ["nome = %s", "email = %s"]
    params = [nome, email]

    if senha:
        senha_hash = hash_password(senha)
        sets.append("senha = %s")
        params.append(senha_hash)

    params.append(user_id)

    sql = f"""
        UPDATE public.usuarios
           SET {', '.join(sets)}
         WHERE id = %s
     RETURNING id, nome, email;
    """

    try:
        rows = db_execute(sql, tuple(params), returning=True)
        if not rows:
            flash("Usuário não encontrado.", "error")
            return redirect(url_for("list_users"))
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("list_users"))
    except psycopg.errors.UniqueViolation:
        flash("Email já cadastrado.", "error")
        return redirect(url_for("user_edit_form", user_id=user_id))
    except Exception as e:
        flash(f"Erro inesperado: {e}", "error")
        return redirect(url_for("user_edit_form", user_id=user_id))

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    # Em produção, use um servidor como gunicorn (cada worker terá seu próprio pool)
    app.run(host="0.0.0.0", port=5000, debug=True)
